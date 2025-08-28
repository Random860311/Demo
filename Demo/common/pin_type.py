from enum import Enum


class EPinType(str, Enum):
    POWER = "POWER"
    PWM = "PWM"
    GENERAL = "GENERAL"
    GROUND = "GROUND"
    RESERVED = "RESERVED"
