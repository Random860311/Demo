import threading
from typing import Dict

from core.event.event_dispatcher import EventDispatcher
from db.dao.motor_dao import MotorDao
from dto.motor_dto import MotorDto
from services.base_service import BaseService
from services.pigpio_service import PigpioService
from servomotor.controller import ControllerPWM
from servomotor.controller_status import EMotorStatus


class ControllerService(BaseService):

    def __init__(self, dispatcher: EventDispatcher, pigpio: PigpioService, motor_dao: MotorDao):
        super().__init__(dispatcher)

        self.__motor_dao = motor_dao
        self.__pigpio_service = pigpio

        self._controller_pool: Dict[int, ControllerPWM] = {}
        self._lock = threading.Lock()

    def _subscribe_to_events(self):
        pass

    def is_any_controller_running(self) -> bool:
        with self._lock:
            for _, controller in self._controller_pool.items():
                if controller.status == EMotorStatus.RUNNING:
                    return True
            return False

    def is_controller_running(self, motor_id: int) -> bool:
        controller = self.get_controller(motor_id)
        return controller.status == EMotorStatus.RUNNING

    def set_all_controllers_home(self):
        with self._lock:
            for _, controller in self._controller_pool.items():
                controller.set_home()

    def set_controller_home(self, motor_id: int):
        controller = self.get_controller(motor_id)
        with self._lock:
            controller.set_home()

    def get_controller_status(self, motor_id: int) -> EMotorStatus:
        controller = self.get_controller(motor_id)
        return controller.status

    def get_controller(self, motor_id: int) -> ControllerPWM:
        with self._lock:
            controller = self._controller_pool.get(motor_id)
            if not controller:
                print(f"Loading motor: {motor_id}")
                motor_model = self.__motor_dao.get_by_id(motor_id)
                config = MotorDao.get_pin_config(motor_id)
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

    def update_controller(self, motor_dto: MotorDto) -> ControllerPWM:
        controller = self.get_controller(motor_dto.id)
        if controller.status == EMotorStatus.RUNNING:
            raise ValueError(f"Motor {motor_dto.id} is already running, cannot update.")
        with self._lock:
            controller.target_freq = motor_dto.target_freq
            controller.duty = motor_dto.duty
        return controller