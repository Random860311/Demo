from dataclasses import dataclass
from typing import Optional

from common.PinType import PinType
from db.model.db_config import db_app

@dataclass
class PinModel:
    physical_pin_number: int
    pigpio_pin_number: Optional[int]
    description: str
    pin_type: PinType

    @property
    def id(self) -> int:
        return self.physical_pin_number


PIN_MAP: dict[int, PinModel] = {
    # physical, bcm, description, pin_type
    1: PinModel(1, None, "3.3V Power", PinType.POWER),
    2: PinModel(2, None, "5V Power", PinType.POWER),
    3: PinModel(3, 2, "SDA1 (GPIO2)", PinType.GENERAL),
    4: PinModel(4, None, "5V Power", PinType.POWER),
    5: PinModel(5, 3, "SCL1 (GPIO3)", PinType.GENERAL),
    6: PinModel(6, None, "Ground", PinType.GROUND),
    7: PinModel(7, 4, "GPIO4", PinType.GENERAL),
    8: PinModel(8, 14, "TXD0 (GPIO14)", PinType.GENERAL),
    9: PinModel(9, None, "Ground", PinType.GROUND),
    10: PinModel(10, 15, "RXD0 (GPIO15)", PinType.GENERAL),
    11: PinModel(11, 17, "GPIO17", PinType.GENERAL),
    12: PinModel(12, 18, "GPIO18 (PCM_CLK)", PinType.PWM),
    13: PinModel(13, 27, "GPIO27", PinType.GENERAL),
    14: PinModel(14, None, "Ground", PinType.GROUND),
    15: PinModel(15, 22, "GPIO22", PinType.GENERAL),
    16: PinModel(16, 23, "GPIO23", PinType.GENERAL),
    17: PinModel(17, None, "3.3V Power", PinType.POWER),
    18: PinModel(18, 24, "GPIO24", PinType.GENERAL),
    19: PinModel(19, 10, "GPIO10 (MOSI)", PinType.GENERAL),
    20: PinModel(20, None, "Ground", PinType.GROUND),
    21: PinModel(21, 9, "GPIO9 (MISO)", PinType.GENERAL),
    22: PinModel(22, 25, "GPIO25", PinType.GENERAL),
    23: PinModel(23, 11, "GPIO11 (SCLK)", PinType.GENERAL),
    24: PinModel(24, 8, "GPIO8 (CE0)", PinType.GENERAL),
    25: PinModel(25, None, "Ground", PinType.GROUND),
    26: PinModel(26, 7, "GPIO7 (CE1)", PinType.GENERAL),
    27: PinModel(27, None, "ID_SD (EEPROM)", PinType.RESERVED),
    28: PinModel(28, None, "ID_SC (EEPROM)", PinType.RESERVED),
    29: PinModel(29, 5, "GPIO5", PinType.GENERAL),
    30: PinModel(30, None, "Ground", PinType.GROUND),
    31: PinModel(31, 6, "GPIO6", PinType.GENERAL),
    32: PinModel(32, 12, "GPIO12", PinType.PWM),
    33: PinModel(33, 13, "GPIO13", PinType.PWM),
    34: PinModel(34, None, "Ground", PinType.GROUND),
    35: PinModel(35, 19, "GPIO19", PinType.PWM),
    36: PinModel(36, 16, "GPIO16", PinType.GENERAL),
    37: PinModel(37, 26, "GPIO26", PinType.GENERAL),
    38: PinModel(38, 20, "GPIO20", PinType.GENERAL),
    39: PinModel(39, None, "Ground", PinType.GROUND),
    40: PinModel(40, 21, "GPIO21", PinType.GENERAL),
}