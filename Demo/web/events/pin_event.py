from enum import Enum
from dataclasses import dataclass
from core.event.base_event import BaseEvent


class EPinEventType(str, Enum):
    GET_ALL = "pin:get_all"
    GET_AVAILABLE = "pin:get_available"

    STATUS_CHANGED = "pin:status_changed"

@dataclass
class PinStatusData:
    pin_id: int
    status: bool

class PinStatusEvent(BaseEvent[list[PinStatusData]]):
    def __init__(self, data: list[PinStatusData]):
        super().__init__(key=EPinEventType.STATUS_CHANGED, data=data)