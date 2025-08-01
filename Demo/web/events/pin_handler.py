from flask_socketio import SocketIO
from services.pin_service import PinService
from web.events.event_types import PinEventType
from web.events.responses import Response, EStatusCode


class PinHandler:
    def __init__(self, socketio: SocketIO, pin_services: PinService):
        self.__socketio = socketio
        self.__pin_service = pin_services

    def register_handlers(self):
        self.__socketio.on_event(message=PinEventType.GET_ALL, handler=self.handle_get_all_pins)
        self.__socketio.on_event(message=PinEventType.GET_AVAILABLE, handler=self.handle_get_available_pins)

    def handle_get_all_pins(self, data):
        dto_list = self.__pin_service.get_all()
        return Response(status_code=EStatusCode.SUCCESS, list_obj=[dto.to_dict() for dto in dto_list]).__dict__
        # return [dto.to_dict() for dto in dto_list]

    def handle_get_available_pins(self, data):
        dto_list = self.__pin_service.get_available_pins()
        return Response(status_code=EStatusCode.SUCCESS, list_obj=[dto.to_dict() for dto in dto_list]).__dict__
        # return [dto.to_dict() for dto in dto_list]

# def register_pin_events(socketio: SocketIO):
#     @socketio.on("pin:get_all")
#     def handle_get_all_pins(data):
#         dto_list = pin_service.get_all()
#         return [dto.to_dict() for dto in dto_list]
#
#     @socketio.on("pin:get_available")
#     def handle_get_available_pins(data):
#         dto_list = pin_service.get_available_pins()
#         return [dto.to_dict() for dto in dto_list]
