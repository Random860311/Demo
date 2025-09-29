from typing import Optional

from dataclasses import dataclass

from servomotor.dto.controller_status import EMotorStatus


@dataclass
class ControllerStatusEvent:
    motor_id: int
    status: EMotorStatus
    freq_hz: int
    direction: Optional[bool] # True => Clockwise, False => Counter-clockwise, None => stopped

@dataclass
class ControllerPositionEvent:
    motor_id: int
    position: int
    delta: int
    direction: Optional[bool]  # True => Clockwise, False => Counter-clockwise, None => stopped