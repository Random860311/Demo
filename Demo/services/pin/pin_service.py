from typing import Optional

from flask_socketio import SocketIO

from core.event.event_dispatcher import EventDispatcher
from db.dao.pin_dao import PinDao
from db.model.pin.pin_model import PinModel
from dto.pin_dto import PinDto
from services.base_service import BaseService
from services.pigpio.pigpio_protocol import PigpioProtocol
from services.pin.pin_protocol import PinProtocol
from web.events.pin_event import PinEvent
from event.pin_status_change_event import PinStatusChangeEvent


class PinService(BaseService, PinProtocol):
    def __init__(self, dispatcher: EventDispatcher, socketio: SocketIO, pigpio: PigpioProtocol):
        super().__init__(dispatcher, socketio)

        self.__pigpio_service = pigpio

        self._subscribe_to_events()

    def get_all(self) -> list[PinDto]:
        pin_models = PinDao.get_all()
        return [self.__create_dto(model) for model in pin_models]

    def get_pin(self, pin_id: int) -> Optional[PinDto]:
        model = PinDao.get_by_id(pin_id)
        return self.__create_dto(model)

    def get_pin_id(self, gpio: int) -> int:
        return PinDao.get_by_gpio_number(gpio).id

    def __create_dto(self, model: PinModel) -> PinDto:
        return PinDto(id=model.id,
                      physical_pin_number=model.physical_pin_number,
                      pigpio_pin_number=model.pigpio_pin_number,
                      pin_type=model.pin_type,
                      description=model.description,
                      status=self.__pigpio_service.get_gpio_pin_status(model.pigpio_pin_number))

    def _handle_pin_status_change(self, event: PinStatusChangeEvent):
        self._dispatcher.emit_async(PinEvent(event))

    def _subscribe_to_events(self):
        self._dispatcher.subscribe(PinStatusChangeEvent, self._handle_pin_status_change)


