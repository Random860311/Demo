from enum import Enum

class EControllerRunMode(int, Enum):
    SINGLE_STEP = 0
    CONFIG = 1
    INFINITE = 2

    @classmethod
    def from_value(cls, value: int, default: "EControllerRunMode" = None) -> "EControllerRunMode":
        try:
            return cls(value)
        except ValueError:
            print("Error: Invalid value for EControllerRunMode: ", value)
            if default is not None:
                return default
            raise