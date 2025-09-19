from enum import Enum
from typing import Optional


class EMotorLabel(str, Enum):
    X = "X"
    Y = "Y"
    Z = "Z"

    @classmethod
    def from_value(cls, value: str, default: "EMotorLabel" = None) -> Optional["EMotorLabel"]:
        try:
            return cls(value)
        except ValueError:
            return default
