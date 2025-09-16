from typing import Any, Unpack

from flask_socketio import SocketIO

from core.event.event_dispatcher import EventDispatcher
from db.model.motor_model import MotorModel
from event.motor_task_event import TaskHomeFinishedEvent, TaskStepFinishedEvent, TaskOriginFinishedEvent
from services.controller.controller_protocol import ControllerProtocol
from services.motor.tasks.base_run_task import BaseRunTask
from services.motor.tasks.find_home_task import FindHomeTask
from services.motor.tasks.move_steps_task import MoveStepsTask
from services.motor.tasks.run_task_protocol import ExecKwargs
from services.pigpio.pigpio_protocol import PigpioProtocol
from servomotor.controller_status import EMotorStatus
from servomotor.event.controller_event import MotorStatusData


class MoveOriginTask(BaseRunTask):
    def __init__(self,
                 controller_service: ControllerProtocol,
                 dispatcher: EventDispatcher,
                 socketio: SocketIO,
                 gpio_service: PigpioProtocol,
                 motor: MotorModel,
                 home_pin_id: int):
        super().__init__(controller_service, dispatcher, motor)

        self.__home_task = FindHomeTask(controller_service=controller_service,
                                        dispatcher=dispatcher,
                                        socketio=socketio,
                                        gpio_service=gpio_service,
                                        motor=motor,
                                        home_pin_id=home_pin_id)

        self.__step_task = MoveStepsTask(controller_service=controller_service,
                                         motor=motor,
                                         dispatcher=dispatcher)

        self.__at_home = False
        self.__running_steps = False

    def _start_steps_task(self):
        if self._controller_service.get_controller_status(self._motor.id) == EMotorStatus.STOPPED:
            self.__running_steps = True
            position = self._controller_service.get_controller_position(self._motor.id)
            steps = self._motor.origin - position

            if steps == 0:
                self._dispatcher.emit_async(TaskOriginFinishedEvent(self._motor.id, self.uuid))
                self.stop()
            else:
                self.__step_task.execute(steps=steps)

    def _handle_home_event(self, event: TaskHomeFinishedEvent):
        if event.task_id == self.__home_task.uuid:
            self.__at_home = True
            self._start_steps_task()

    def _handle_steps_event(self, event: TaskHomeFinishedEvent):
        if event.task_id == self.__step_task.uuid:
            self.stop()
            self._dispatcher.emit_async(TaskOriginFinishedEvent(self._motor.id, self.uuid))

    def handle_controller_status_change(self, event: MotorStatusData):
        super().handle_controller_status_change(event)
        if (event.motor_id == self.controller_id) and (self.is_finished is False) and (event.status == EMotorStatus.STOPPED and self.__at_home):
            self._start_steps_task()

    def execute(self, **kwargs: Unpack[ExecKwargs]) -> None:
        super().execute(**{**kwargs, "pass_limits": False})

        if self._motor.origin == self._motor.position:
            self.stop()
        else:
            self._dispatcher.subscribe(TaskHomeFinishedEvent, self._handle_home_event)
            self._dispatcher.subscribe(TaskStepFinishedEvent, self._handle_steps_event)


            self.__at_home = False
            self.__running_steps = False

            self.__home_task.execute()


    def stop(self):
        super().stop()

        self.__at_home = False
        self.__running_steps = False

        self.__home_task.stop()
        self.__step_task.stop()

        self._dispatcher.unsubscribe(TaskHomeFinishedEvent, self._handle_home_event)
        self._dispatcher.unsubscribe(TaskStepFinishedEvent, self._handle_steps_event)