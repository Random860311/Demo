from enum import Enum

class MotorEventType(str, Enum):
    GET_ALL = "motor:get_all"
    UPDATE = "motor:update"
    STOP = "motor:stop"
    START = "motor:start"
    UPDATED = "motor:updated"

class PinEventType(str, Enum):
    GET_ALL = "pin:get_all"
    GET_AVAILABLE = "pin:get_available"