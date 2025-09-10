from typing import Optional

from core.event.base_event import BaseEvent
from dataclasses import dataclass

from servomotor.controller_status import EMotorStatus


@dataclass
class MotorStatusData:
    motor_id: int
    status: EMotorStatus
    position: int

    forward: Optional[bool] = None
