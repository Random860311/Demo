from dataclasses import dataclass
from typing import Optional, Any
from common.pin_type import EPinType
from core.serializable import Serializable


@dataclass
class PinDto(Serializable):
    id: int
    physical_pin_number: int
    pigpio_pin_number: Optional[int]
    pin_type: EPinType
    description: str
    status: bool = False

    @staticmethod
    def from_dict(data: dict) -> "PinDto":
        return PinDto(**data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "physical_pin_number": self.physical_pin_number,
            "pigpio_pin_number": self.pigpio_pin_number,
            "pin_type": self.pin_type,
            "description": self.description,
            "status": self.status
        }

    # "pin_type": self.pin_type.value,