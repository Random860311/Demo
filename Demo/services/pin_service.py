import time
from typing import Optional

from flask_socketio import SocketIO

from core.event.event_dispatcher import EventDispatcher
from db.dao.pin_dao import PinDao
from db.model.pin_model import PinModel
from dto.pin_dto import PinDto
from services.base_service import BaseService
from services.pigpio_service import PigpioService
from web.events.pin_event import PinStatusEvent, PinStatusData


class PinService(BaseService):

    def __init__(self, dispatcher: EventDispatcher, pigpio: PigpioService, socketio: SocketIO):
        super().__init__(dispatcher)

        self.__pigpio_service = pigpio
        self.__socketio = socketio
        self.__listening = False

    def get_all(self) -> list[PinDto]:
        pin_models = PinDao.get_all()
        return [self.__create_dto(model) for model in pin_models]

    def get_pin(self, pin_id: int) -> Optional[PinDto]:
        model = PinDao.get_by_id(pin_id)
        return self.__create_dto(model)

    def __create_dto(self, model: PinModel) -> PinDto:
        return PinDto(id=model.id,
                      physical_pin_number=model.physical_pin_number,
                      pigpio_pin_number=model.pigpio_pin_number,
                      pin_type=model.pin_type,
                      description=model.description,
                      status=self.__pigpio_service.get_gpio_pin_status(model.pigpio_pin_number))

    def start_listening_pins(self) -> None:
        if self.__listening:
            return
        self.__listening = True
        self.__socketio.start_background_task(self.__start_updates)

    def stop_listening_pins(self) -> None:
        self.__listening = False

    def __start_updates(self) -> None:
        while self.__listening:
            status = self.__pigpio_service.get_gpio_status()
            data = [PinStatusData(pin_id=key, status=value) for key, value in status.items()]
            self._dispatcher.emit(PinStatusEvent(data))

            time.sleep(0.5)

    def _subscribe_to_events(self):
        pass

    @staticmethod
    def to_dto(pin: PinModel) -> PinDto:
        return PinDto(
            id=pin.id,
            physical_pin_number=pin.physical_pin_number,
            pigpio_pin_number=pin.pigpio_pin_number,
            pin_type=pin.pin_type,
            description=pin.description,
        )
