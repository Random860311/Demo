from dataclasses import dataclass
from typing import List


@dataclass
class MotorConfigDto:
    id: int
    pin_step: int
    pin_forward: int
    pin_enable: int
    total_steps: int
    target_freq: int
    duty: float
    start_freq: int
    accel_steps: int
    decel_steps: int
    loops: int

    @staticmethod
    def from_list(data: list) -> List["MotorConfigDto"]:
        return [MotorConfigDto(**motor) for motor in data]