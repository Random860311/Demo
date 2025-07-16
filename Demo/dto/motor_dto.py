from dataclasses import dataclass
from typing import List
from dto.pin_dto import PinDto

@dataclass
class MotorDto:
    id: int
    pin_step: PinDto
    pin_forward: PinDto
    pin_enable: PinDto
    total_steps: int
    target_freq: int
    duty: float
    start_freq: int
    accel_steps: int
    decel_steps: int
    loops: int

    @staticmethod
    def from_list(data: list) -> List["MotorDto"]:
        return [MotorDto(**motor) for motor in data]