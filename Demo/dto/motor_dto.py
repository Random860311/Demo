from dataclasses import dataclass
from typing import List, Any, Optional

from core.serializable import Serializable
from dto.pin_dto import PinDto
from servomotor.controller_status import EMotorStatus


@dataclass
class MotorDto(Serializable):
    id: int
    name: str
    angle: float
    target_freq: int
    duty: float

    position: int
    #home: Optional[int] = None
    origin: Optional[int] = None
    limit: Optional[int] = None

    status: EMotorStatus = EMotorStatus.STOPPED

    pin_step: Optional[PinDto] = None
    pin_forward: Optional[PinDto] = None
    pin_enable: Optional[PinDto] = None
    pin_home: Optional[PinDto] = None

    distance_per_turn: float = 0

    # This motor should rotate clockwise from position 0
    clockwise: bool = True
    # Movement direction
    direction: Optional[bool] = None

    @staticmethod
    def from_dict(data: dict) -> "MotorDto":
        return MotorDto(
            id=data["id"],
            name=data["name"],
            pin_step=PinDto.from_dict(data["pin_step"]) if data.get("pin_step") else None,
            pin_forward=PinDto.from_dict(data["pin_forward"]) if data.get("pin_forward") else None,
            pin_enable=PinDto.from_dict(data["pin_enable"]) if data.get("pin_enable") else None,
            # pin_home=PinDto.from_dict(data["pin_home"]) if data.get("pin_home") else None,
            angle=data["angle"],
            target_freq=data["target_freq"],
            duty=data["duty"],
            distance_per_turn=data.get("distance_per_turn", 0),
            position=data.get("position", 0),
            origin=data.get("origin", None),
            # home=data.get("home", None),
            status=EMotorStatus(data.get("status", EMotorStatus.STOPPED))
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
            "pin_home": self.pin_home.to_dict() if self.pin_home else None,

            "angle": self.angle,
            "target_freq": self.target_freq,
            "duty": self.duty,
            "distance_per_turn": self.distance_per_turn,
            "status": self.status,

            "position": self.position,
            "origin": self.origin,
            # "home": self.home,
            "limit": self.limit,

            "clockwise": self.clockwise,
            "direction": self.direction,
        }