from flask_socketio import SocketIO

from core.event.event_dispatcher import EventDispatcher
from services.pin_service import PinService
from web.events.pin_event import EPinEventType, PinStatusEvent
from web.events.response import Response, EStatusCode
from web.handlers.base_handler import BaseHandler


class PinHandler(BaseHandler):
    def __init__(self, dispatcher: EventDispatcher, socketio: SocketIO, pin_services: PinService):
        super().__init__(dispatcher, socketio)

        self.__pin_service = pin_services

    def register_handlers(self):
        self._socketio.on_event(message=EPinEventType.GET_ALL, handler=self.handle_get_all_pins)
        self._socketio.on_event(message=EPinEventType.GET_AVAILABLE, handler=self.handle_get_all_pins)

        self._dispatcher.subscribe(PinStatusEvent, self._emit_event)

    def handle_get_all_pins(self, data):
        dto_list = self.__pin_service.get_all()
        return Response(status_code=EStatusCode.SUCCESS, list_obj=[dto.to_dict() for dto in dto_list]).__dict__