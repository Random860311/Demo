from typing import Any, Unpack, Optional

from core.event.event_dispatcher import EventDispatcher
from db.model.motor.motor_model import MotorModel
from event.motor_task_event import TaskStepFinishedEvent
from services.controller.controller_protocol import ControllerProtocol
from services.motor.tasks.base_task import BaseSingleMotorTask
from services.motor.tasks.task_protocol import ExecKwargs
from servomotor.controller_status import EMotorStatus
from servomotor.event.controller_event import MotorStatusData


class MoveStepsTask(BaseSingleMotorTask):
    def __init__(self, controller_service: ControllerProtocol, motor: MotorModel, dispatcher: EventDispatcher, **kwargs: Any):
        super().__init__(controller_service, dispatcher)

        self.__motor = motor
        self.__steps = kwargs.get("steps", 0)
        self.__direction = kwargs.get("direction", self.motor.clockwise)

    @property
    def motor(self) -> MotorModel:
        return self.__motor

    @property
    def _steps(self) -> Optional[int]:
        return self.__steps

    @property
    def current_direction(self) -> Optional[bool]:
        return self.__direction

    def handle_controller_status_change(self, event: MotorStatusData):
        super().handle_controller_status_change(event)
        if (event.motor_id == self.motor.id) and (self.is_finished is False) and (event.status == EMotorStatus.STOPPED):
            self.stop()
            self._dispatcher.emit_async(TaskStepFinishedEvent(self.uuid, self.motor.id))

    def execute(self, **kwargs: Unpack[ExecKwargs]) -> None:
        self.__steps = kwargs.get("steps", self.__steps)
        self.__direction = kwargs.get("direction", self.__direction)

        super().execute(**kwargs)

        print(f"Steps task id: {self.motor.id} steps: {self.__steps} direction: {self.__direction} freq: {self.freq_hz}")
        self._controller_service.start_controller(controller_id=self.motor.id, steps=self.__steps, freq_hz=self.freq_hz, forward=self.__direction)

    def stop(self):
        super().stop()
