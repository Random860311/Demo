from dataclasses import dataclass
from enum import Enum

from core.event.base_event import BaseEvent
from dto.motor_dto import MotorDto


class EMotorEventType(str, Enum):
    GET_ALL = "motor:get_all"                   # Request to retrieve all motors
    UPDATE = "motor:update"                     # Request to update motor
    STOP = "motor:stop"                         # Request to stop motor
    START = "motor:start"                       # Request to start motor
    UPDATED = "motor:updated"                   # Broadcast motor updated
    STATUS_CHANGED = "motor:status_changed"     # Broadcast motor status changed
    POSITION_CHANGED = "motor:position_changed" # Broadcast motor position changed

class MotorUpdatedEvent(BaseEvent[MotorDto]):
    def __init__(self, data: MotorDto):
        super().__init__(key=EMotorEventType.UPDATED, data=data)