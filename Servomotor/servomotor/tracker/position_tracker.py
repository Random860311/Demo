from threading import RLock
from typing import Optional
import time
from core.dao.base_motor_dao import BaseMotorDao
from core.event.event_dispatcher import EventDispatcher


class PositionTracker:
    def __init__(self, motor_id: int, motor_dao: BaseMotorDao, events_dispatcher: EventDispatcher):
        self._pos_lock = RLock()
        self._motion_lock = RLock()
        self._motor_dao = motor_dao

        self._motor_id: int = motor_id
        self._current_steps = motor_dao.get_motor_position(self._motor_id)

        # motion context
        self._active: bool = False
        self._programmed_steps: int = 0             # 0 = unbounded (for infinite run)
        self._dir_sign: int = 1                     # +1 fwd, -1 rev
        self._start_ts: Optional[float] = None      # monotonic start
        self._freq_hz: Optional[float] = None
        self._applied_steps: int = 0                # steps already applied since start
        self._events_dispatcher = events_dispatcher

    def save(self):
        try:
            print("Updating motor: ", self._motor_id, " position: ", self._current_steps)
            self._motor_dao.update_motor_position(self._motor_id, self._current_steps)
        except Exception as e:
            print(f"Failed to update motor: {self._motor_id} position: {self._current_steps}", e)

    def set_home(self) -> None:
        with self._pos_lock:
            self._current_steps = 0
        self.save()

    def get_steps(self) -> int:
        with self._pos_lock:
            return self._current_steps

    def begin_motion(self, programmed_steps: int, forward: bool, freq_hz: float) -> None:
        """
        programmed_steps: intended steps for this run; 0 => unbounded (infinite).
        forward: True => +1, False => -1
        freq_hz: step frequency used by controller
        """
        if freq_hz <= 0:
            raise ValueError(f"freq_hz must be > 0, got {freq_hz}")

        with self._motion_lock:
            self._active = True
            self._programmed_steps = max(0, int(programmed_steps))
            self._dir_sign = +1 if forward else -1
            self._freq_hz = float(freq_hz)
            self._start_ts = time.monotonic()
            self._applied_steps = 0

    def tick(self, now_ts: Optional[float] = None) -> int:
        """
        Public on-demand update. Call this as often as required (e.g., every 5 ms).
        Updates _current_steps in memory ONLY (no DB write). Returns applied delta.
        """
        with self._motion_lock:
            if not self._active or self._start_ts is None or self._freq_hz is None:
                return 0

            if now_ts is None:
                now_ts = time.monotonic()

            delta = self._compute_delta_steps(now_ts)
            if delta <= 0:
                return 0

            with self._pos_lock:
                self._current_steps += self._dir_sign * delta

            self._applied_steps += delta

            return delta

    def finish_motion(self, save: bool = True) -> None:
        """Call after PWM stops or on abort to account actual steps from elapsed time * freq."""
        with self._motion_lock:
            if not self._active or self._start_ts is None or self._freq_hz is None:
                return

            # flush any remaining delta
            self.tick(time.monotonic())

            # reset context
            self._active = False
            self._programmed_steps = 0
            self._dir_sign = +1
            self._start_ts = None
            self._freq_hz = None

            if save:
                self.save()

    def _compute_delta_steps(self, now_ts: float) -> int:
        """
        Compute how many new steps to apply since start (delta = total_est - applied),
        respecting programmed_steps if bounded. Assumes motion_lock is held.
        """
        assert self._start_ts is not None and self._freq_hz is not None

        elapsed = max(0.0, now_ts - self._start_ts)
        est_total = int(round(elapsed * self._freq_hz))  # total estimated since start
        delta = est_total - self._applied_steps  # new steps not yet applied

        if delta <= 0:
            return 0

        if self._programmed_steps > 0:
            remaining = self._programmed_steps - self._applied_steps
            if remaining <= 0:
                return 0
            delta = min(delta, remaining)

        return delta