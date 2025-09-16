from flask_socketio import SocketIO

from core.event.event_dispatcher import EventDispatcher
from dto.config_dto import ConfigDto
from services.config.config_protocol import ConfigProtocol
from web.events.config_event import EConfigEventType, ConfigEvent
from web.events.response import EStatusCode, Response
from web.handlers.base_handler import BaseHandler

class ConfigHandler(BaseHandler):
    def __init__(self, dispatcher: EventDispatcher, socketio: SocketIO, config_services: ConfigProtocol):
        super().__init__(dispatcher, socketio)
        self.__config_service = config_services

    def register_handlers(self):
        self._socketio.on_event(message=EConfigEventType.GET_ALL, handler=self.handle_get_all)
        self._socketio.on_event(message=EConfigEventType.UPDATE, handler=self.handle_update)
        self._socketio.on_event(message=EConfigEventType.GET, handler=self.handle_get)
        self._socketio.on_event(message=EConfigEventType.DELETE, handler=self.handle_delete)

    def handle_get_all(self, data):
        try:
            dto_list = self.__config_service.get_all()
            configs = [dto.to_dict() for dto in dto_list]

            return Response(status_code=EStatusCode.SUCCESS, list_obj=configs).__dict__
        except Exception as e:
            print("Error in ConfigHandler, handle_get_all: ", str(e))
            return Response(status_code=EStatusCode.ERROR, message="Error fetching configs.").__dict__

    def handle_update(self, data):
        try:
            dto = ConfigDto.from_dict(data)
            updated_dto = self.__config_service.save_or_update(dto)

            event = ConfigEvent(key=EConfigEventType.UPDATED, data=updated_dto)
            self._emit_event(event)

            return Response(status_code=EStatusCode.SUCCESS).__dict__
        except Exception as e:
            print("Error in ConfigHandler, handle_update: ", str(e))
            return Response(status_code=EStatusCode.ERROR, message="Error updating config.").__dict__

    def handle_get(self, data):
        try:
            config_id = data.get("configId")
            if id is None:
                raise Exception("Config id is required to update")
            dto = self.__config_service.get_by_id(config_id)

            return Response(status_code=EStatusCode.SUCCESS, obj=dto.to_dict()).__dict__
        except Exception as e:
            print("Error in ConfigHandler, handle_update: ", str(e))
            return Response(status_code=EStatusCode.ERROR, message="Error updating config.").__dict__

    def handle_delete(self, data):
        try:
            config_id = data.get("configId")
            if id is None:
                raise Exception("Config id is required to delete")
            deleted_dto = self.__config_service.delete(config_id)

            event = ConfigEvent(key=EConfigEventType.DELETED, data=deleted_dto)
            self._emit_event(event)

            return Response(status_code=EStatusCode.SUCCESS).__dict__
        except Exception as e:
            print("Error in ConfigHandler, handle_update: ", str(e))
            return Response(status_code=EStatusCode.ERROR, message="Error updating config.").__dict__