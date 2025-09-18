import threading
from typing import Dict

from flask_socketio import SocketIO

from core.event.event_dispatcher import EventDispatcher
from db.dao.motor_dao import MotorDao
from dto.motor_dto import MotorDto
from services.base_service import BaseService
from services.controller.controller_protocol import ControllerProtocol
from services.pigpio.pigpio_protocol import PigpioProtocol

from servomotor.controller import ControllerPWM
from servomotor.controller_status import EMotorStatus


class ControllerService(BaseService, ControllerProtocol):

    def __init__(self, dispatcher: EventDispatcher, socketio: SocketIO, pigpio: PigpioProtocol, motor_dao: MotorDao):
        super().__init__(dispatcher, socketio)

        self.__motor_dao = motor_dao
        self.__pigpio_service = pigpio

        self._controller_pool: Dict[int, ControllerPWM] = {}
        self._lock = threading.RLock()

    def _subscribe_to_events(self):
        pass

    def start_controller(self, controller_id: int, steps: int, forward: bool = True):
        controller = self.__get_controller(controller_id)
        controller.run(forward=forward, steps=steps)

    def start_controller_async(self, controller_id: int, steps: int, forward: bool = True):
        return self._socketio.start_background_task(self.start_controller, controller_id, steps, forward)

    def stop_controller(self, controller_id: int) -> bool:
        controller = self.__get_controller(controller_id)
        return controller.stop()

    def stop_all_controllers(self) -> None:
        with self._lock:
            controllers = list(self._controller_pool.values())
        for controller in controllers:
            controller.stop()

    def is_any_controller_running(self) -> bool:
        with self._lock:
            controllers = list(self._controller_pool.values())
        for controller in controllers:
            if controller.status == EMotorStatus.RUNNING:
                return True
        return False

    def is_controller_running(self, motor_id: int) -> bool:
        controller = self.__get_controller(motor_id)
        return controller.status == EMotorStatus.RUNNING

    def set_controller_home(self, motor_id: int):
        with self._lock:
            controller = self._controller_pool.get(motor_id)
        if controller is None:
            controller = self.__get_controller(motor_id)   # will create if missing (lock-safe)
        controller.set_home()

    def get_controller_position(self, motor_id: int) -> int:
        controller = self.__get_controller(motor_id)
        return controller.get_position_steps()

    def get_controller_status(self, motor_id: int) -> EMotorStatus:
        controller = self.__get_controller(motor_id)
        return controller.status

    def update_controller(self, motor_dto: MotorDto) -> ControllerPWM:
        controller = self.__get_controller(motor_dto.id)
        if controller.status == EMotorStatus.RUNNING:
            raise ValueError(f"Motor is already running, cannot update.")
        controller.target_freq = motor_dto.target_freq
        controller.duty = motor_dto.duty
        return controller

    def __get_controller(self, motor_id: int) -> ControllerPWM:
        with self._lock:
            controller = self._controller_pool.get(motor_id)
            if not controller:
                motor_model = self.__motor_dao.get_by_id(motor_id)
                config = self.__motor_dao.get_pin_config(motor_id)

                print(f"Creating controller for motor: {motor_id}")
                controller = ControllerPWM(
                    dispatcher=self._dispatcher,
                    pi=self.__pigpio_service.get_pi(),
                    controller_id=motor_id,
                    current_position=motor_model.position,
                    pin_enable= config.enable.pigpio_pin_number,
                    pin_forward= config.dir.pigpio_pin_number,
                    pin_step= config.steps.pigpio_pin_number,
                    target_freq=int(motor_model.target_freq),
                    duty=motor_model.duty,
                )
                self._controller_pool[motor_id] = controller
                print(f"Controller for motor: {motor_id} created.")

            if not controller.pi or not controller.pi.connected:
                print(f"Reconnecting pigpio in controller {motor_id}")
                controller.pi = self.__pigpio_service.get_pi()
            return controller

