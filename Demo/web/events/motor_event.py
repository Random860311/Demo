from dataclasses import dataclass
from enum import Enum

from core.event.base_event import BaseEvent
from dto.motor_dto import MotorDto


class EMotorEventType(str, Enum):
    GET_ALL = "motor:get_all"                   # Request to retrieve all motors
    UPDATE = "motor:update"                     # Request to update motor
    STOP = "motor:stop"                         # Request to stop motor
    START = "motor:start"                       # Request to start motor

    SET_ORIGIN_ALL = "motor:set_origin_all"     # Request to set all motors origins
    SET_ORIGIN = "motor:set_origin"             # Request to set motors origins

    SET_LIMIT_ALL = "motor:set_limit_all"       # Request to set all motors limits
    SET_LIMIT = "motor:set_limit"               # Request to set motors limits

    MOVE_TO_HOME = "motor:move_to_home"
    MOVE_TO_ORIGIN = "motor:move_to_origin"

    SET_CALIBRATION = "motor:set_calibration"
    GET_CALIBRATION = "motor:get_calibration"
    CALIBRATION_CHANGED = "motor:calibration_changed"

    UPDATED = "motor:updated"                   # Broadcast motor updated
    STATUS_CHANGED = "motor:status_changed"     # Broadcast motor status changed
    POSITION_CHANGED = "motor:position_changed" # Broadcast motor position changed

    START_GCODE = "motor:start_gcode"


class MotorUpdatedEvent(BaseEvent[MotorDto]):
    def __init__(self, data: MotorDto):
        super().__init__(key=EMotorEventType.UPDATED, data=data)

class CalibrationChangedEvent(BaseEvent[dict]):
    def __init__(self, calibration: bool):
        super().__init__(key=EMotorEventType.CALIBRATION_CHANGED, data={"calibrate": calibration})