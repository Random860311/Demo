import threading
from threading import RLock
from typing import Optional
import time

from core.event.event_dispatcher import EventDispatcher
from core.thread_manager import ThreadManagerProtocol
from servomotor.event.controller_event import ControllerPositionEvent


class PositionTracker:
    def __init__(self, controller_id: int, dispatcher: EventDispatcher,  thread_manager: ThreadManagerProtocol):
        self.__pos_lock = RLock()
        self.__motion_lock = RLock()

        self.__thread_manager = thread_manager
        self._event_dispatcher = dispatcher

        self.__controller_id = controller_id
        self.__current_steps = 0

        # motion context
        self.__stop_event = threading.Event()
        self.__active: bool = False
        self.__dir_sign: int = 1                     # +1 fwd, -1 rev
        self.__start_ts: Optional[float] = None      # monotonic start
        self.__freq_hz: Optional[float] = None
        self.__applied_steps: int = 0                # steps have already applied since start

    @property
    def controller_id(self) -> int:
        return self.__controller_id

    @property
    def position(self) -> int:
        with self.__pos_lock:
            return self.__current_steps

    def set_home(self) -> None:
        with self.__pos_lock:
            self.__current_steps = 0

        self._event_dispatcher.emit_async(ControllerPositionEvent(
            motor_id=self.__controller_id,
            position=0,
            delta=0,
            direction=True if self.__dir_sign > 0 else False)
        )

    def begin_motion(self, current_position: int, forward: bool, freq_hz: float) -> None:
        """
        programmed_steps: intended steps for this run; 0 => unbounded (infinite).
        forward: True => +1, False => -1
        freq_hz: step frequency used by controller
        """
        if freq_hz <= 0:
            raise ValueError(f"freq_hz must be > 0, got {freq_hz}")

        if self.__active:
            print(f"PositionTracker for motor {self.__controller_id} is already running.")
            return

        self.__stop_event.clear()

        with self.__motion_lock:
            self.__active = True
            self.__current_steps = current_position
            self.__dir_sign = +1 if forward else -1
            self.__freq_hz = float(freq_hz)
            self.__start_ts = time.monotonic()
            self.__applied_steps = 0

        self.__thread_manager.start_background_task(self.__start_thread)

    def finish_motion(self) -> None:
        """Call after PWM stops or on abort to account actual steps from elapsed time * freq."""
        with self.__motion_lock:
            self.__stop_event.set()
            if not self.__active or self.__start_ts is None or self.__freq_hz is None:
                return

            # flush any remaining delta
            self.__tick(time.monotonic())

            # reset context
            self.__active = False
            self.__dir_sign = +1
            self.__start_ts = None
            self.__freq_hz = None

    def __start_thread(self):
        while not self.__stop_event.is_set() and self.__active:
            self.__tick()
            self.__stop_event.wait(0.05)

    def __tick(self, now_ts: Optional[float] = None) -> int:
        """
        Public on-demand update. Call this as often as required (e.g., every 5 ms).
        Updates _current_steps in memory. Returns applied delta.
        """
        with self.__motion_lock:
            if not self.__active or self.__start_ts is None or self.__freq_hz is None:
                return 0

            if now_ts is None:
                now_ts = time.monotonic()

            delta = self.__compute_delta_steps(now_ts)
            if delta <= 0:
                return 0

            with self.__pos_lock:
                self.__current_steps += self.__dir_sign * delta

            self.__applied_steps += delta

            self._event_dispatcher.emit_async(ControllerPositionEvent(
                motor_id=self.__controller_id,
                position=self.__current_steps,
                delta=delta,
                direction=True if self.__dir_sign > 0 else False)
            )

            return delta

    def __compute_delta_steps(self, now_ts: float) -> int:
        """
        Compute how many new steps to apply since start (delta = total_est - applied),
        respecting programmed_steps if bounded. Assumes motion_lock is held.
        """
        assert self.__start_ts is not None and self.__freq_hz is not None

        elapsed = max(0.0, now_ts - self.__start_ts)
        est_total = int(round(elapsed * self.__freq_hz))  # total estimated since start
        delta = est_total - self.__applied_steps  # new steps not yet applied

        return 0 if delta <= 0 else delta