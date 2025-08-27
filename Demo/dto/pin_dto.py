from dataclasses import dataclass
from typing import Optional, Any
from common.PinType import PinType
from core.serializable import Serializable


@dataclass
class PinDto(Serializable):
    id: int
    physical_pin_number: int
    pigpio_pin_number: Optional[int]
    pin_type: PinType
    description: str

    @staticmethod
    def from_dict(data: dict) -> "PinDto":
        return PinDto(**data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "physical_pin_number": self.physical_pin_number,
            "pigpio_pin_number": self.pigpio_pin_number,
            "pin_type": self.pin_type if isinstance(self.pin_type, str) else self.pin_type.value,
            "description": self.description,
        }

    # "pin_type": self.pin_type.value,