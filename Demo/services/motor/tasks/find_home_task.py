import threading
from typing import Any, Unpack

from flask_socketio import SocketIO

from core.event.event_dispatcher import EventDispatcher
from db.model.motor_model import MotorModel
from event.motor_task_event import TaskHomeFinishedEvent
from event.pin_status_change_event import PinStatusChangeEvent
from services.controller.controller_protocol import ControllerProtocol
from services.motor.tasks.base_run_task import BaseRunTask
from services.motor.tasks.run_task_protocol import ExecKwargs
from services.pigpio.pigpio_protocol import PigpioProtocol


class FindHomeTask(BaseRunTask):
    def __init__(self,
                 controller_service: ControllerProtocol,
                 dispatcher: EventDispatcher,
                 socketio: SocketIO,
                 gpio_service: PigpioProtocol,
                 motor: MotorModel,
                 home_pin_id: int):
        super().__init__(controller_service, dispatcher, motor)

        self.__socketio = socketio
        self.__gpio_service = gpio_service

        self.__home_pin_id = home_pin_id
        # Initially move back
        self.__direction = not motor.clockwise
        self.__top_reached = False

        self.__abort_event = threading.Event()

    def _start_adjustment(self):
        self.__abort_event.clear()

        self.__top_reached = True
        self.__direction = not self.__direction

        while not self.__abort_event.is_set():
            self._controller_service.start_controller(self._motor.id, 1, forward=self.__direction)
            self.__abort_event.wait(0.1)

    def handle_pin_status_change(self, event: PinStatusChangeEvent):
        if event.pin_id != self.__home_pin_id or self.is_finished is not False:
            return
        if not event.status and not self.__top_reached:
            self._controller_service.stop_controller(self._motor.id)
            self.__socketio.start_background_task(self._start_adjustment)
        elif event.status and self.__top_reached:
            self.stop()
            self._dispatcher.emit_async(TaskHomeFinishedEvent(self._motor.id, self.uuid))

    def execute(self, **kwargs: Unpack[ExecKwargs]) -> None:
        super().execute(**{**kwargs, "pass_limits": True})

        at_home = not self.__gpio_service.get_pin_status(self.__home_pin_id)

        if at_home:
            self._start_adjustment()
        else:
            self._controller_service.start_controller(self._motor.id, 0, forward=self.__direction)

    def stop(self):
        self.__abort_event.set()
        super().stop()