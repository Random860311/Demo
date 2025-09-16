from abc import ABC
import uuid
from typing import Optional, Any, Unpack

from core.event.event_dispatcher import EventDispatcher
from db.model.motor_model import MotorModel
from error.app_warning import AppWarning
from event.pin_status_change_event import PinStatusChangeEvent
from services.controller.controller_protocol import ControllerProtocol
from services.motor.tasks.run_task_protocol import RunTaskProtocol, ExecKwargs
from servomotor.event.controller_event import MotorStatusData


class BaseRunTask(RunTaskProtocol, ABC):
    def __init__(self, controller_service: ControllerProtocol, dispatcher: EventDispatcher, motor: MotorModel):
        self._controller_service = controller_service
        self._dispatcher = dispatcher

        self._motor = motor
        self._uuid = uuid.uuid4()

        self._is_finished: Optional[bool] = None

        self._pass_limits = False

    @property
    def uuid(self):
        return self._uuid

    @property
    def controller_id(self):
        return self._motor.id

    @property
    def is_finished(self) -> Optional[bool]:
        """
        Indicates whether the task has finished.

        :return: None-> Task has not started, True-> Task has finished, False-> Task is running.
        :rtype: Optional[bool]
        """
        return self._is_finished

    @property
    def _steps(self) -> Optional[int]:
        return None

    def execute(self, **kwargs: Unpack[ExecKwargs]) -> None:
        if self._controller_service.is_controller_running(self._motor.id):
            raise ValueError("Cannot start a controller that is already running.")

        pass_limits = kwargs.get("pass_limits", False)

        self._validate_operation()
        self._pass_limits = pass_limits
        self._is_finished = False

    def stop(self):
        self._is_finished = True

    def _validate_operation(self, current_position: Optional[int] = None):
        try:
            if not self._pass_limits:
                if self._motor.limit is None:
                    raise AppWarning(f"Motor '{self._motor.name}' does not have limit set.")
                if self._motor.origin is None:
                    raise AppWarning(f"Motor '{self._motor.name}' does not have origin set.")

                final_position: Optional[int] = (
                    None if current_position is None
                    else current_position + (0 if self._steps is None else self._steps)
                )

                if final_position is not None:
                    if self._motor.clockwise:
                        if self._motor.limit and final_position >= self._motor.limit:
                            raise AppWarning(f"Motor '{self._motor.name}' is at limit or the limit will be surpassed and can't continue running in clockwise direction.")
                        if final_position < self._motor.origin:
                            raise AppWarning(f"Motor '{self._motor.name}' is at origin or the origin position be surpassed and can't continue running in clockwise direction.")
                    else:
                        if self._motor.limit and final_position <= self._motor.limit:
                            raise AppWarning(f"Motor '{self._motor.name}' is at limit or the limit will be surpassed and can't continue running in counter-clockwise direction.")
                        if final_position > self._motor.origin:
                            raise AppWarning(f"Motor '{self._motor.name}' is at origin or the origin position be surpassed and can't continue running in counter-clockwise direction.")
        except AppWarning as ew:
            self.stop()
            raise ew

    def handle_pin_status_change(self, event: PinStatusChangeEvent) -> None:
        pass

    def handle_controller_status_change(self, event: MotorStatusData) -> None:
        if event.motor_id != self._motor.id or self.is_finished is False:
            return
        self._validate_operation(event.position)
