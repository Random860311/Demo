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
