from flask_socketio import SocketIO

from core.event.event_dispatcher import EventDispatcher
from db.dao.config_dao import ConfigDao
from db.model.config_model import ConfigModel
from dto.config_dto import ConfigDto
from services.base_service import BaseService
from services.config.config_protocol import ConfigProtocol


class ConfigService(BaseService, ConfigProtocol):
    def __init__(self, dispatcher: EventDispatcher, socketio: SocketIO, config_dao: ConfigDao):
        super().__init__(dispatcher, socketio)
        self.__config_dao = config_dao

    def get_by_id(self, obj_id: int) -> ConfigDto:
        model = self.__config_dao.get_by_id(obj_id)
        if model is None:
            raise ValueError(f"Config with id {obj_id} not found")

        return ConfigDto(model.id, model.value_x, model.value_y, model.value_z)

    def get_all(self) -> list[ConfigDto]:
        models = self.__config_dao.get_all()
        return [ConfigDto(model.id, model.value_x, model.value_y, model.value_z) for model in models]

    def save_or_update(self, dto: ConfigDto) -> ConfigDto:
        model = ConfigModel()
        model.id = dto.id
        model.value_x = dto.value_x
        model.value_y = dto.value_y
        model.value_z = dto.value_z

        updated_model = self.__config_dao.save_or_update(model)
        return ConfigDto(updated_model.id, updated_model.value_x, updated_model.value_y, updated_model.value_z)

    def delete(self, obj_id: int) -> ConfigDto:
        deleted_model = self.__config_dao.delete(obj_id)
        return ConfigDto(deleted_model.id, deleted_model.value_x, deleted_model.value_y, deleted_model.value_z)