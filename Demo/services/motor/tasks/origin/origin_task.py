from typing import Unpack, Optional

from core.event.event_dispatcher import EventDispatcher
from db.model.motor.motor_model import MotorModel
from event.motor_event import TaskOriginFinishedEvent
from services.controller.controller_protocol import ControllerServiceProtocol
from services.motor.tasks.base_task import BaseSingleMotorTask
from services.motor.tasks.task_protocol import ExecKwargs
from servomotor.dto.controller_status import EMotorStatus


class MoveOriginTask(BaseSingleMotorTask):
    def __init__(self,
                 controller_service: ControllerServiceProtocol,
                 dispatcher: EventDispatcher,
                 motor: MotorModel):
        super().__init__(controller_service, dispatcher)

        self.__motor = motor
        self.__direction: Optional[bool] = None
        self.__steps: Optional[int] = None

    @property
    def motor(self) -> MotorModel:
        return self.__motor

    @property
    def _steps(self) -> Optional[int]:
        return self.__steps

    @property
    def direction(self) -> Optional[bool]:
        return self.__direction

    def handle_controller_status_change(self, event: MotorEvent):
        super().handle_controller_status_change(event)
        if (event.motor_id == self.motor.id) and (self.is_finished is False) and (event.status == EMotorStatus.STOPPED):
            self.stop()
            self._dispatcher.emit_async(TaskOriginFinishedEvent(self.uuid, self.motor.id))

    def execute(self, **kwargs: Unpack[ExecKwargs]) -> None:
        if self.motor.origin == self.motor.position:
            self.stop()
            self._dispatcher.emit_async(TaskOriginFinishedEvent(self.uuid, self.motor.id))
            return

        self.__direction = self.motor.origin > self.motor.position
        self.__steps = abs(self.motor.origin - self.motor.position)

        super().execute(**kwargs)
        self._controller_service.start(controller_id=self.motor.id, steps=self.__steps, freq_hz=self.freq_hz, forward=self.__direction)

