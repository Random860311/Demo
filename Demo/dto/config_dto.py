from dataclasses import dataclass
from typing import Optional, Any

from core.serializable import Serializable

@dataclass
class ConfigDto(Serializable):
    id: int
    value_x: Optional[float]
    value_y: Optional[float]
    value_z: Optional[float]

    @staticmethod
    def from_dict(data: dict) -> "ConfigDto":
        return ConfigDto(
            id=data["id"],
            value_x=data.get("value_x"),
            value_y=data.get("value_y"),
            value_z=data.get("value_z"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "value_x": self.value_x,
            "value_y": self.value_y,
            "value_z": self.value_y,
        }