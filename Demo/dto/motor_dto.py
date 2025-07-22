from dataclasses import dataclass
from typing import List
from dto.pin_dto import PinDto

@dataclass
class MotorDto:
    id: int
    name: str
    pin_step: PinDto|None
    pin_forward: PinDto|None
    pin_enable: PinDto|None
    angle: float
    target_freq: float
    duty: float
    start_freq: float
    accel_steps: int
    decel_steps: int
    loops: float = 1
    total_steps: int = 0

    @staticmethod
    def from_list(data: list) -> List["MotorDto"]:
        return [MotorDto(**motor) for motor in data]