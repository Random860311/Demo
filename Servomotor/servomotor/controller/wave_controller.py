from typing import Unpack

from core.event.event_dispatcher import EventDispatcher
from core.thread_manager import ThreadManagerProtocol
from servomotor.controller.base_controller import BaseController
import pigpio
from math import gcd
from functools import reduce

from servomotor.controller.controller_protocol import RunKwargs
from servomotor.dto.controller_status import EMotorStatus
from servomotor.dto.run_cmd_dto import ControllerRunDto


class WavePWMController(BaseController):
    """
    Build and execute composite pigpio wave chains so multiple motors
    complete exactly their step targets in one G-code move.

    Usage per move:
        ctrl = WavePWMController(pi)
        ctrl.run(motors=[MotorRun(...), ...], pulse_us=5)
    """

    def is_motor_in_use(self, motor_id: int) -> bool:
        pass

    def _emit_status_update(self):
        pass

    # -------------------- lifecycle --------------------
    def __init__(self, dispatcher: EventDispatcher, pi: pigpio.pi, thread_manager: ThreadManagerProtocol):
        super().__init__(dispatcher, pi, thread_manager)

        self.__created_wave_ids: list[int] = []
        self.__chain: list[int] = []
        self.__period_us_by_pin: dict[int, int] = {}
        self.__full_frame_cache: dict[frozenset[int], tuple[int, dict[int, int]]] = {}
        self.__frame_len_us: int = 0  # LCM frame

    def stop(self) -> None:
        """Immediate stop of any running chain and put pins safe (STEP low)."""
        self.pi.wave_tx_stop()

        self.status = EMotorStatus.STOPPED

        self.pi.wave_clear()  # resets internal wave ids to 0.. again

        self.__created_wave_ids.clear()
        self.__chain.clear()
        self.__full_frame_cache.clear()

        # Set STEP pins low
        for pin in self.__period_us_by_pin.keys():
            self.pi.write(pin, 0)

    # -------------------- public API --------------------
    def run(self, **kwargs: Unpack[RunKwargs]) -> None:
        """
        Execute ONE G-code move: build a composite chain and transmit.
        Motors with steps==0 are ignored.
        """

        # Filter work
        motors = [m for m in kwargs.get("run_cmd", []) if m.steps > 0]
        if not motors:
            return
        pulse_us = kwargs.get("pulse_us", 5)

        try:
            # 1) Reset pigpio waves and our caches
            self.stop()
            self._abort_event.clear()

            # 2) Compute per-pin periods and the LCM frame
            self._compute_periods_and_frame(motors)
            self._assert_pulse_width(pulse_us)

            # 3) Plan the chain (fills self._chain and self._created_wave_ids)
            self._plan_chain(motors, pulse_us)

            # 4) Transmit and wait
            self.pi.wave_chain(self.__chain)
            self.status = EMotorStatus.RUNNING

            while self.pi.wave_tx_busy():
                self._abort_event.wait(0.005)
                #time.sleep(0.005)
        finally:
            self.stop()

    # -------------------- math helpers --------------------
    @staticmethod
    def _lcm(a: int, b: int) -> int:
        if a == 0 or b == 0:
            return 0
        return abs(a // gcd(a, b) * b)

    @staticmethod
    def _lcm_many(values: list[int]) -> int:
        assert values, "LCM requires at least one value"
        return reduce(WavePWMController._lcm, values)

    def _compute_periods_and_frame(self, motors: list[ControllerRunDto]) -> None:
        """Compute period (µs) per STEP pin and the macro-frame LCM in µs."""
        self.__period_us_by_pin = {
            m.gpio_step: int(round(1_000_000 / m.freq_hz)) for m in motors
        }
        self.__frame_len_us = self._lcm_many(list(self.__period_us_by_pin.values()))

    def _assert_pulse_width(self, pulse_us: int) -> None:
        min_period = min(self.__period_us_by_pin.values())
        if pulse_us <= 0 or pulse_us >= min_period:
            raise ValueError(f"pulse_us={pulse_us} must be >0 and < min period ({min_period} µs)")

    # -------------------- wave building --------------------
    def _build_frame_wave(
            self,
            subset_periods_us: dict[int, int],
            pulse_us: int,
            frame_len_us: int,
            cap_pulses_by_pin: dict[int, int] | None = None,
    ) -> tuple[int, dict[int, int]]:
        """
        Build ONE frame wave lasting exactly frame_len_us microseconds.

        subset_periods_us: {pin -> period_us} for active motors in this frame.
        cap_pulses_by_pin: optional {pin -> max pulses} to schedule in this frame
                           (used for the final partial frame of a segment).
        Returns: (wave_id, scheduled_pulses_by_pin)
        """
        events: list[tuple[int, int]] = []  # (time_us, +/- pin_mask)
        scheduled_by_pin: dict[int, int] = {}

        for pin, T in subset_periods_us.items():
            pulses_in_full = frame_len_us // T
            want = pulses_in_full if cap_pulses_by_pin is None else min(
                pulses_in_full, cap_pulses_by_pin.get(pin, 0)
            )
            scheduled_by_pin[pin] = want
            for k in range(want):
                t_on = k * T
                mask = 1 << pin
                events.append((t_on, mask))  # ON
                events.append((t_on + pulse_us, -mask))  # OFF

        # No events? Create a dummy wait frame, useful for edge cases
        if not events:
            self.pi.wave_add_generic([pigpio.pulse(0, 0, frame_len_us)])
            wave_id = self.pi.wave_create()
            self._assert_wave_id(wave_id)
            self.__created_wave_ids.append(wave_id)
            return wave_id, {pin: 0 for pin in subset_periods_us.keys()}

        # Consolidate by time
        by_time: dict[int, tuple[int, int]] = {}  # t -> (on_mask, off_mask)
        for t, m in events:
            on_mask, off_mask = by_time.get(t, (0, 0))
            if m > 0:
                on_mask |= m
            else:
                off_mask |= (-m)
            by_time[t] = (on_mask, off_mask)

        # Build pulses
        pulses: list[pigpio.pulse] = []
        last_t = 0
        for t in sorted(by_time.keys()):
            gap = t - last_t
            if gap > 0:
                pulses.append(pigpio.pulse(0, 0, gap))
            on_mask, off_mask = by_time[t]
            if on_mask:
                pulses.append(pigpio.pulse(on_mask, 0, 0))
            if off_mask:
                pulses.append(pigpio.pulse(0, off_mask, 0))
            last_t = t
        tail = frame_len_us - last_t
        if tail > 0:
            pulses.append(pigpio.pulse(0, 0, tail))

        self.pi.wave_add_generic(pulses)
        wave_id = self.pi.wave_create()
        self._assert_wave_id(wave_id)
        self.__created_wave_ids.append(wave_id)
        return wave_id, scheduled_by_pin

    def _get_full_frame_wave_for_subset(
            self, pins_subset: list[int], pulse_us: int
    ) -> tuple[int, dict[int, int]]:
        """
        Returns (wave_id, frame_pulses_by_pin) for this subset of pins.
        Caches per subset so we reuse the same wave id within this run().
        """
        key = frozenset(pins_subset)
        cached = self.__full_frame_cache.get(key)
        if cached:
            return cached

        subset_periods = {p: self.__period_us_by_pin[p] for p in pins_subset}
        wave_id, frame_counts = self._build_frame_wave(
            subset_periods_us=subset_periods,
            pulse_us=pulse_us,
            frame_len_us=self.__frame_len_us,
            cap_pulses_by_pin=None,
        )
        self.__full_frame_cache[key] = (wave_id, frame_counts)
        return wave_id, frame_counts

    # -------------------- chain planning & helpers --------------------
    @staticmethod
    def _split_loop_count(n: int) -> list[int]:
        """Split large loop counts into 16-bit-safe chunks (1..65535) for wave_chain."""
        parts: list[int] = []
        while n > 0:
            chunk = min(n, 65535)
            parts.append(chunk)
            n -= chunk
        return parts

    @staticmethod
    def _loop_cmd(wave_id: int, repeat: int) -> list[int]:
        """Encode: 'play wave_id; then repeat it N times'."""
        lo = repeat & 0xFF
        hi = (repeat >> 8) & 0xFF
        return [255, 0, wave_id, 255, 1, lo, hi] #[wave_id, 255, 0, lo, hi]

    @staticmethod
    def _assert_wave_id(wave_id: int) -> None:
        if not (0 <= wave_id <= 250):
            # wave_chain can only encode ids 0..250
            raise RuntimeError(f"wave_create returned id {wave_id}, cannot be chained")

    def _plan_chain(self, motors: list[ControllerRunDto], pulse_us: int) -> None:
        """
        Build self._chain by sequencing full-frame loops and at-most-one partial frame
        for each active subset until all pins reach zero remaining steps.
        """
        remaining_by_pin: dict[int, int] = {m.gpio_step: m.steps for m in motors}

        while True:
            active_pins = [p for p, rem in remaining_by_pin.items() if rem > 0]
            if not active_pins:
                break

            # 1) Full-frame for current subset
            wave_id_full, frame_counts = self._get_full_frame_wave_for_subset(
                active_pins, pulse_us=pulse_us
            )

            # How many full frames can we loop before any motor finishes?
            frames_max = min(
                (remaining_by_pin[p] // frame_counts[p]) if frame_counts[p] > 0 else 0
                for p in active_pins
            )

            if frames_max > 0:
                for chunk in self._split_loop_count(frames_max):
                    self.__chain += self._loop_cmd(wave_id_full, chunk)
                for p in active_pins:
                    remaining_by_pin[p] -= frame_counts[p] * frames_max
                continue

            # 2) Final partial frame for this subset (schedule only the leftovers)
            caps = {p: min(remaining_by_pin[p], frame_counts[p]) for p in active_pins}
            subset_periods = {p: self.__period_us_by_pin[p] for p in active_pins}
            partial_wave_id, scheduled = self._build_frame_wave(
                subset_periods_us=subset_periods,
                pulse_us=pulse_us,
                frame_len_us=self.__frame_len_us,
                cap_pulses_by_pin=caps,
            )
            self.__chain.append(partial_wave_id)
            for p in active_pins:
                remaining_by_pin[p] -= scheduled[p]

