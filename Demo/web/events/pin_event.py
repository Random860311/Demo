from enum import Enum


class PinEventType(str, Enum):
    GET_ALL = "pin:get_all"
    GET_AVAILABLE = "pin:get_available"
