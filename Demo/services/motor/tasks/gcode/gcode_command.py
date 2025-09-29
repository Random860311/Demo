from enum import Enum
from typing import Optional


class EGcodeCommand(str, Enum):
    G0 = "G0"
    G1 = "G1"
    G2 = "G2"

    @classmethod
    def from_value(cls, value: str, default: "EGcodeCommand" = None) -> Optional["EGcodeCommand"]:
        try:
            return cls(value)
        except ValueError:
            return default
