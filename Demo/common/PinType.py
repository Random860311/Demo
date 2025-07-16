from enum import Enum


class PinType(str, Enum):
    POWER = "POWER"
    PWM = "PWM"
    GENERAL = "GENERAL"
    GROUND = "GROUND"
    RESERVED = "RESERVED"
