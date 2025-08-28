import pigpio

from core.event.event_dispatcher import EventDispatcher
from db.dao.motor_dao import MotorDao
from dto.motor_dto import MotorDto
from common import utils
from servomotor.controller import ControllerPWM
from servomotor.controller_status import EMotorStatus
from typing import Dict, Optional
import threading

class PigpioService:
    gpio_pins = list(range(28))

    def __init__(self, motor_dao: MotorDao, dispatcher: EventDispatcher):
        self.__event_dispatcher = dispatcher
        self.__pi = pigpio.pi()
        self._controller_pool: Dict[int, ControllerPWM] = {}
        self._lock = threading.Lock()
        self._motor_dao = motor_dao

    def get_pi(self) -> pigpio.pi:
        if not self.__pi.connected:
            print("Reconnecting pigpio...")
            self.__pi = pigpio.pi()

        return self.__pi

    def get_gpio_pin_status(self, gpio: Optional[int]) -> bool:
        if not gpio in PigpioService.gpio_pins:
            return False
        pi = self.get_pi()
        return pi.read(gpio)

    def get_gpio_status(self) -> dict[int, bool]:
        status: dict[int, bool] = {}
        for gpio in PigpioService.gpio_pins:
            status[gpio] = (self.get_gpio_pin_status(gpio))
        return status

    def get_controller_status(self, motor_id: int) -> EMotorStatus:
        controller = self.get_controller(motor_id)
        return controller.status

    def get_controller(self, motor_id: int) -> ControllerPWM:
        with self._lock:
            controller = self._controller_pool.get(motor_id)
            if not controller:
                print(f"Loading motor: {motor_id}")
                motor_model = self._motor_dao.get_by_id(motor_id)
                total_turns = utils.calculate_motor_total_turns(motor_model.turns, motor_model.distance, motor_model.distance_per_turn)
                total_steps = utils.calculate_motor_total_steps(motor_model.angle, total_turns)

                print(f"Creating controller for motor: {motor_id}")
                controller = ControllerPWM(
                    dispatcher=self.__event_dispatcher,
                    pi=self.get_pi(),
                    controller_id=motor_id,
                    current_position=motor_model.position,
                    pin_enable= -1 if not motor_model.pin_enable else motor_model.pin_enable.pigpio_pin_number,
                    pin_forward= -1 if not motor_model.pin_forward else motor_model.pin_forward.pigpio_pin_number,
                    pin_step= -1 if not motor_model.pin_step else motor_model.pin_step.pigpio_pin_number,
                    total_steps=total_steps,
                    target_freq=int(motor_model.target_freq),
                    duty=motor_model.duty,
                )
                self._controller_pool[motor_id] = controller
                print(f"Controller for motor: {motor_id} created.")

            if not controller.pi or not controller.pi.connected:
                print(f"Reconnecting pigpio in controller {motor_id}")
                controller.pi = self.get_pi()
            return controller

    def update_controller(self, motor_dto: MotorDto) -> ControllerPWM:
        controller = self.get_controller(motor_dto.id)
        if controller.status == EMotorStatus.RUNNING:
            raise ValueError(f"Motor {motor_dto.id} is already running, cannot update.")
        with self._lock:
            # controller.pin_enable = -1 if not motor_dto.pin_enable else motor_dto.pin_enable.pigpio_pin_number
            # controller.pin_forward = -1 if not motor_dto.pin_forward else motor_dto.pin_forward.pigpio_pin_number
            # controller.pin_step = -1 if not motor_dto.pin_step else motor_dto.pin_step.pigpio_pin_number
            controller.target_freq = motor_dto.target_freq
            controller.duty = motor_dto.duty
            controller.total_steps = motor_dto.total_steps
            controller.duty = motor_dto.duty
        return controller
