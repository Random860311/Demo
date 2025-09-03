from enum import Enum

from core.event.base_event import BaseEvent
from dto.config_dto import ConfigDto


class EConfigEventType(str, Enum):
    GET_ALL = "config:get_all"
    UPDATE = "config:update"
    GET = "config:get"
    DELETE = "config:delete"

    UPDATED = "config:updated"
    DELETED = "config:deleted"

class ConfigEvent(BaseEvent[ConfigDto]):
    def __init__(self, key: EConfigEventType, data: ConfigDto):
        super().__init__(key=key, data=data)