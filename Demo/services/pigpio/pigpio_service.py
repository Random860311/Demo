import pigpio

from typing import Optional

from flask_socketio import SocketIO

from core.di_container import container
from core.event.event_dispatcher import EventDispatcher
from db.dao.motor_dao import MotorDao
from db.dao.pin_dao import PinDao
from event.pin_event import PinStatusChangeEvent
from services.base_service import BaseService
from services.pigpio.pigpio_protocol import PigpioProtocol


class PigpioService(BaseService, PigpioProtocol):
    def __init__(self, dispatcher: EventDispatcher, socketio: SocketIO):
        super().__init__(dispatcher, socketio)

        self.__configure_gpio()

    def __configure_gpio(self):
        print("Configuring pigpio...")
        self.__pi = pigpio.pi()
        configs = MotorDao.get_all_pin_configs()

        for config in configs:
            self.__pi.set_mode(config.steps.pigpio_pin_number, pigpio.OUTPUT)
            self.__pi.set_mode(config.dir.pigpio_pin_number, pigpio.OUTPUT)
            self.__pi.set_mode(config.enable.pigpio_pin_number, pigpio.OUTPUT)

            # self.__pi.set_mode(config.home, pigpio.INPUT)
            self.__pi.set_pull_up_down(config.home.pigpio_pin_number, pigpio.PUD_UP)

            self.__add_callback(config.steps.pigpio_pin_number)
            self.__add_callback(config.dir.pigpio_pin_number)
            self.__add_callback(config.enable.pigpio_pin_number)
            self.__add_callback(config.home.pigpio_pin_number)

    def __add_callback(self, gpio):
        self.__pi.callback(gpio, pigpio.EITHER_EDGE, self._handle_pin_status)
        self.__pi.set_glitch_filter(gpio, 5000)

    def get_pi(self) -> pigpio.pi:
        if not self.__pi.connected:
            self.__configure_gpio()
        return self.__pi

    def get_pin_status(self, pin_id: int) -> bool:
        gpio = PinDao.get_by_id(pin_id).pigpio_pin_number
        return self.get_gpio_pin_status(gpio)

    def get_gpio_pin_status(self, gpio: Optional[int]) -> bool:
        if not gpio in list(range(28)):
            return False
        pi = self.get_pi()
        return pi.read(gpio)

    def get_gpio_status(self) -> dict[int, bool]:
        status: dict[int, bool] = {}
        for gpio in list(range(28)):
            status[gpio] = (self.get_gpio_pin_status(gpio))
        return status

    def _handle_pin_status(self, gpio: int, level: int, tick) -> None:
        # level: 0=falling to low, 1=rising to high, 2=watchdog timeout
        # print(f"Pin {gpio} status changed to {level}")
        pin_id = PinDao.get_by_gpio_number(gpio).id

        self._dispatcher.emit_async(PinStatusChangeEvent(pin_id=pin_id, pigpio_pin_number=gpio, status=level == 1))

