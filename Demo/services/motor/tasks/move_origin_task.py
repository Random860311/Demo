from typing import Any, Unpack, Optional

from core.event.event_dispatcher import EventDispatcher
from db.model.motor_model import MotorModel
from event.motor_task_event import TaskOriginFinishedEvent
from services.controller.controller_protocol import ControllerProtocol
from services.motor.tasks.base_run_task import BaseSingleMotorTask
from services.motor.tasks.run_task_protocol import ExecKwargs
from services.pigpio.pigpio_protocol import PigpioProtocol
from servomotor.controller_status import EMotorStatus
from servomotor.event.controller_event import MotorStatusData


class MoveOriginTask(BaseSingleMotorTask):
    def __init__(self,
                 controller_service: ControllerProtocol,
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
    def current_direction(self) -> Optional[bool]:
        return self.__direction

    def handle_controller_status_change(self, event: MotorStatusData):
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
        self._controller_service.start_controller(self.motor.id, steps=self.__steps, forward=self.__direction)

