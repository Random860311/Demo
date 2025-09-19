from abc import ABC, abstractmethod
import uuid
from typing import Optional, Unpack

from core.event.event_dispatcher import EventDispatcher
from db.model.motor.motor_model import MotorModel
from error.app_warning import AppWarning
from event.pin_status_change_event import PinStatusChangeEvent
from services.controller.controller_protocol import ControllerProtocol
from services.motor.tasks.task_protocol import SingleMotorTaskProtocol, ExecKwargs, MotorTaskProtocol
from servomotor.event.controller_event import MotorStatusData

class BaseMotorTask(MotorTaskProtocol, ABC):
    def __init__(self, controller_service: ControllerProtocol, dispatcher: EventDispatcher):
        self._controller_service = controller_service
        self._dispatcher = dispatcher

        self._uuid = uuid.uuid4()
        self._execute_kwargs: Unpack[ExecKwargs] = {}
        self._is_finished: Optional[bool] = None

    @property
    def uuid(self):
        return self._uuid

    @property
    def is_finished(self) -> Optional[bool]:
        """
        Indicates whether the task has finished.

        :return: None-> Task has not started, True-> Task has finished, False-> Task is running.
        :rtype: Optional[bool]
        """
        return self._is_finished

    def execute(self, **kwargs: Unpack[ExecKwargs]) -> None:
        self._is_finished = False
        self._execute_kwargs = kwargs

    def stop(self):
        self._is_finished = True

    def handle_pin_status_change(self, event: PinStatusChangeEvent) -> None:
        pass

    def handle_controller_status_change(self, event: MotorStatusData) -> None:
        pass

class BaseSingleMotorTask(SingleMotorTaskProtocol, BaseMotorTask, ABC):
    def __init__(self, controller_service: ControllerProtocol, dispatcher: EventDispatcher):
        super().__init__(controller_service, dispatcher)

        self._pass_limits = False

    @property
    @abstractmethod
    def motor(self) -> MotorModel:
        pass

    @property
    def freq_hz(self) -> int:
        return self._execute_kwargs.get("freq_hz", self.motor.target_freq)

    @property
    def controller_id(self):
        return self.motor.id

    @property
    def current_direction(self) -> Optional[bool]:
        return None

    @property
    def _steps(self) -> Optional[int]:
        return None

    def execute(self, **kwargs: Unpack[ExecKwargs]) -> None:
        if self._controller_service.is_controller_running(self.motor.id):
            raise ValueError("Cannot start a controller that is already running.")

        self._pass_limits = kwargs.get("pass_limits", False)
        current_position = kwargs.get("current_position", self.motor.position)

        self._validate_operation(current_position=current_position)
        super().execute(**kwargs)

    def _validate_operation(self, current_position: Optional[int] = None, check_final_position: bool = True):
        try:
            if not self._pass_limits:
                if self.motor.limit is None:
                    raise AppWarning(f"Motor '{self.motor.name}' does not have limit set.")
                if self.motor.origin is None:
                    raise AppWarning(f"Motor '{self.motor.name}' does not have origin set.")

                final_position: Optional[int] = None
                if current_position is not None:
                    final_position = current_position
                    if (self._steps is not None) and check_final_position:
                        final_position += self._steps

                if final_position is not None:
                    if self.motor.clockwise:
                        if (self.current_direction is True) and self.motor.limit and (final_position >= self.motor.limit):
                            raise AppWarning(f"Motor '{self.motor.name}' is at limit or the limit will be surpassed and can't continue running in clockwise direction.")
                        if (self.current_direction is False) and (final_position < self.motor.origin):
                            raise AppWarning(f"Motor '{self.motor.name}' is at origin or the origin position will be surpassed and can't continue running in clockwise direction.")
                    else:
                        if (self.current_direction is False) and self.motor.limit and (final_position <= self.motor.limit):
                            raise AppWarning(f"Motor '{self.motor.name}' is at limit or the limit will be surpassed and can't continue running in counter-clockwise direction.")
                        if (self.current_direction is True) and (final_position > self.motor.origin):
                            raise AppWarning(f"Motor '{self.motor.name}' is at origin or the origin position will be surpassed and can't continue running in counter-clockwise direction.")
        except AppWarning as ew:
            self.stop()
            raise ew



    def handle_controller_status_change(self, event: MotorStatusData) -> None:
        if event.motor_id != self.motor.id or self.is_finished is not False:
            return
        self._validate_operation(event.position, check_final_position = False)
