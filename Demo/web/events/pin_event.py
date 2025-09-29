from enum import Enum
from core.event.base_event import BaseEvent
from event.pin_event import PinStatusChangeEvent


class EPinEventType(str, Enum):
    GET_ALL = "pin:get_all"
    GET_AVAILABLE = "pin:get_available"

    STATUS_CHANGED = "pin:status_changed"


class PinEvent(BaseEvent[PinStatusChangeEvent]):
    def __init__(self, data: PinStatusChangeEvent):
        super().__init__(key=EPinEventType.STATUS_CHANGED, data=data)