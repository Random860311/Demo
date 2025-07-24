from dataclasses import dataclass
from typing import Optional
from common.PinType import PinType


@dataclass
class PinDto:
    id: int
    physical_pin_number: int
    pigpio_pin_number: Optional[int]
    pin_type: PinType
    description: str
    in_use: bool

    @staticmethod
    def from_dict(data: dict) -> "PinDto":
        return PinDto(**data)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "physical_pin_number": self.physical_pin_number,
            "pigpio_pin_number": self.pigpio_pin_number,
            "pin_type": self.pin_type.value,
            "description": self.description,
            "in_use": self.in_use,
        }