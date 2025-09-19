import threading
from typing import Unpack, Optional

from flask_socketio import SocketIO

from core.event.event_dispatcher import EventDispatcher
from db.model.motor.motor_model import MotorModel
from event.motor_task_event import TaskHomeFinishedEvent
from event.pin_status_change_event import PinStatusChangeEvent
from services.controller.controller_protocol import ControllerProtocol
from services.motor.tasks.base_task import BaseSingleMotorTask
from services.motor.tasks.task_protocol import ExecKwargs
from services.pigpio.pigpio_protocol import PigpioProtocol


class FindHomeTask(BaseSingleMotorTask):
    def __init__(self,
                 controller_service: ControllerProtocol,
                 dispatcher: EventDispatcher,
                 socketio: SocketIO,
                 gpio_service: PigpioProtocol,
                 motor: MotorModel,
                 home_pin_id: int):
        super().__init__(controller_service, dispatcher)

        self.__motor = motor

        self.__socketio = socketio
        self.__gpio_service = gpio_service

        self.__home_pin_id = home_pin_id
        # Initially move back
        self.__direction = not motor.clockwise
        self.__top_reached = False

        self.__abort_event = threading.Event()

    @property
    def motor(self) -> MotorModel:
        return self.__motor

    @property
    def current_direction(self) -> Optional[bool]:
        return self.__direction

    def _start_adjustment(self):
        self.__abort_event.clear()

        self.__top_reached = True
        self.__direction = not self.__direction

        while not self.__abort_event.is_set():
            self._controller_service.start_controller(controller_id=self.motor.id, steps=1, freq_hz=self.freq_hz, forward=self.__direction)
            self.__abort_event.wait(0.1)

    def handle_pin_status_change(self, event: PinStatusChangeEvent):
        if event.pin_id != self.__home_pin_id or self.is_finished is not False:
            return
        if not event.status and not self.__top_reached:
            self._controller_service.stop_controller(self.motor.id)
            self.__socketio.start_background_task(self._start_adjustment)
        elif event.status and self.__top_reached:
            self.stop()
            self._dispatcher.emit_async(TaskHomeFinishedEvent(self.uuid, self.motor.id))

    def execute(self, **kwargs: Unpack[ExecKwargs]) -> None:
        super().execute(**{**kwargs, "pass_limits": True})

        at_home = not self.__gpio_service.get_pin_status(self.__home_pin_id)

        if at_home:
            self._start_adjustment()
        else:
            self._controller_service.start_controller(controller_id=self.motor.id, steps=0, freq_hz=self.freq_hz, forward=self.__direction)

    def stop(self):
        self.__abort_event.set()
        super().stop()