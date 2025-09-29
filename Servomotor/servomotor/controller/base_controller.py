from abc import ABC, abstractmethod
from typing import Unpack

import pigpio
import threading
from core.event.event_dispatcher import EventDispatcher
from core.thread_manager import ThreadManagerProtocol
from servomotor.controller.controller_protocol import ControllerProtocol, RunKwargs
from servomotor.dto.controller_status import EMotorStatus


class BaseController(ControllerProtocol, ABC):
    def __init__(self, dispatcher: EventDispatcher, pi: pigpio.pi, thread_manager: ThreadManagerProtocol):
        self._event_dispatcher = dispatcher
        self._thread_manager = thread_manager

        self.__pi = pi
        self.__status = EMotorStatus.STOPPED

        self._abort_event = threading.Event()

    @property
    def pi(self) -> pigpio.pi:
        return self.__pi

    @pi.setter
    def pi(self, value: pigpio.pi):
        self.__pi = value

    @property
    def status(self) -> EMotorStatus:
        return self.__status

    @status.setter
    def status(self, value: EMotorStatus):
        if self.__status == value:
            return
        self.__status = value
        self._emit_status_update()

    @abstractmethod
    def stop(self) -> bool:
        pass

    @abstractmethod
    def run(self, **kwargs: Unpack[RunKwargs]):
        pass

    @abstractmethod
    def is_motor_in_use(self, motor_id: int) -> bool:
        pass

    def _start_position_updates(self):
        # emit every 50 ms while RUNNING, but break immediately if aborted
        while self.__status == EMotorStatus.RUNNING:
            # compute current position in memory
            self._emit_status_update()

            # interruptible sleep (breaks instantly when stop() sets the event)
            if self._abort_event.wait(0.01):
                break

    @abstractmethod
    def _emit_status_update(self):
        pass



