from typing import Any


class Serializable:
    def to_dict(self) -> dict[str, Any]:
        return self.__dict__