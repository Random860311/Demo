from typing import Any, Unpack, Optional

from flask_socketio import SocketIO

from core.event.event_dispatcher import EventDispatcher
from db.model.motor_model import MotorModel
from event.motor_task_event import TaskStepFinishedEvent
from services.controller.controller_protocol import ControllerProtocol
from services.motor.tasks.base_run_task import BaseRunTask
from services.motor.tasks.run_task_protocol import ExecKwargs
from servomotor.controller_status import EMotorStatus
from servomotor.event.controller_event import MotorStatusData


class MoveStepsTask(BaseRunTask):
    def __init__(self, controller_service: ControllerProtocol, motor: MotorModel, dispatcher: EventDispatcher, **kwargs: Any):
        super().__init__(controller_service, dispatcher, motor)

        self.__steps = kwargs.get("steps", 0)
        self.__direction = kwargs.get("direction", self._motor.clockwise)

    @property
    def _steps(self) -> Optional[int]:
        return self.__steps

    def handle_controller_status_change(self, event: MotorStatusData):
        super().handle_controller_status_change(event)
        if (event.motor_id == self._motor.id) and (self.is_finished is False) and (event.status == EMotorStatus.STOPPED):
            self.stop()
            self._dispatcher.emit_async(TaskStepFinishedEvent(self._motor.id, self.uuid))

    def execute(self, **kwargs: Unpack[ExecKwargs]) -> None:
        super().execute(**kwargs)

        self.__steps = kwargs.get("steps", self.__steps)
        self.__direction = kwargs.get("direction", self.__direction)

        self._controller_service.start_controller(self._motor.id, steps=self.__steps, forward=self.__direction)

    def stop(self):
        super().stop()
