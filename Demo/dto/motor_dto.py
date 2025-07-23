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
    def from_dict(data: dict) -> "MotorDto":
        return MotorDto(
            id=data["id"],
            name=data["name"],
            pin_step=PinDto.from_dict(data["pin_step"]) if data.get("pin_step") else None,
            pin_forward=PinDto.from_dict(data["pin_forward"]) if data.get("pin_forward") else None,
            pin_enable=PinDto.from_dict(data["pin_enable"]) if data.get("pin_enable") else None,
            angle=data["angle"],
            target_freq=data["target_freq"],
            duty=data["duty"],
            start_freq=data["start_freq"],
            accel_steps=data["accel_steps"],
            decel_steps=data["decel_steps"],
            loops=data.get("loops", 1),
            total_steps=data.get("total_steps", 0),
        )

    @staticmethod
    def from_list(data: list) -> List["MotorDto"]:
        return [MotorDto.from_dict(**motor) for motor in data]