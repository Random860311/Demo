from dataclasses import dataclass
from typing import List, Any

from core.serializable import Serializable
from dto.pin_dto import PinDto
from common import utils

@dataclass
class MotorDto(Serializable):
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

    turns: float = 1
    distance: float = 0
    distance_per_turn: float = 0

    @property
    def total_steps(self) -> int:
        return utils.calculate_motor_total_steps(self.angle, self.total_turns)

    @property
    def total_turns(self) -> float:
        return utils.calculate_motor_total_turns(self.turns, self.distance, self.distance_per_turn)

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
            turns=data.get("turns", 1),
            distance=data.get("distance", 0),
            distance_per_turn=data.get("distance_per_turn", 0),
        )

    @staticmethod
    def from_list(data: list) -> List["MotorDto"]:
        return [MotorDto.from_dict(**motor) for motor in data]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "pin_step": self.pin_step.to_dict() if self.pin_step else None,
            "pin_forward": self.pin_forward.to_dict() if self.pin_forward else None,
            "pin_enable": self.pin_enable.to_dict() if self.pin_enable else None,
            "angle": self.angle,
            "target_freq": self.target_freq,
            "duty": self.duty,
            "start_freq": self.start_freq,
            "accel_steps": self.accel_steps,
            "decel_steps": self.decel_steps,
            "distance": self.distance,
            "distance_per_turn": self.distance_per_turn,
            "turns": self.total_turns,
            "total_steps": self.total_steps,
        }