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