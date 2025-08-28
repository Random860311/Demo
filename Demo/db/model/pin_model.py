from dataclasses import dataclass
from typing import Optional

from common.pin_type import EPinType
from db.model.db_config import db_app

@dataclass
class PinModel:
    physical_pin_number: int
    pigpio_pin_number: Optional[int]
    description: str
    pin_type: EPinType

    @property
    def id(self) -> int:
        return self.physical_pin_number


PIN_MAP: dict[int, PinModel] = {
    # physical, bcm, description, pin_type
    1: PinModel(1, None, "3.3V Power", EPinType.POWER),
    2: PinModel(2, None, "5V Power", EPinType.POWER),
    3: PinModel(3, 2, "GPIO 02 (I2C1 SDA)", EPinType.GENERAL),
    4: PinModel(4, None, "5V Power", EPinType.POWER),
    5: PinModel(5, 3, "GPIO 03 (I2C1 SCL)", EPinType.GENERAL),
    6: PinModel(6, None, "Ground", EPinType.GROUND),
    7: PinModel(7, 4, "GPIO 04 (GPCLK0)", EPinType.GENERAL),
    8: PinModel(8, 14, "GPIO 14 (UART TX)", EPinType.GENERAL),
    9: PinModel(9, None, "Ground", EPinType.GROUND),
    10: PinModel(10, 15, "GPIO 15 (UART RX)", EPinType.GENERAL),
    11: PinModel(11, 17, "GPIO 17", EPinType.GENERAL),
    12: PinModel(12, 18, "GPIO 18 (PCM CLK)", EPinType.PWM),
    13: PinModel(13, 27, "GPIO 27", EPinType.GENERAL),
    14: PinModel(14, None, "Ground", EPinType.GROUND),
    15: PinModel(15, 22, "GPIO 22", EPinType.GENERAL),
    16: PinModel(16, 23, "GPIO 23", EPinType.GENERAL),
    17: PinModel(17, None, "3.3V Power", EPinType.POWER),
    18: PinModel(18, 24, "GPIO 24", EPinType.GENERAL),
    19: PinModel(19, 10, "GPIO 10 (SPI0 MOSI)", EPinType.GENERAL),
    20: PinModel(20, None, "Ground", EPinType.GROUND),
    21: PinModel(21, 9, "GPI O9 (SPI0 MISO)", EPinType.GENERAL),
    22: PinModel(22, 25, "GPIO 25", EPinType.GENERAL),
    23: PinModel(23, 11, "GPIO 11 (SPI0 SCLK)", EPinType.GENERAL),
    24: PinModel(24, 8, "GPI O8 (SPI0 CE0)", EPinType.GENERAL),
    25: PinModel(25, None, "Ground", EPinType.GROUND),
    26: PinModel(26, 7, "GPIO O7 (SPI0 CE1)", EPinType.GENERAL),
    27: PinModel(27, 0, "GPIO 00 (EEFROM SDA)", EPinType.RESERVED),
    28: PinModel(28, 1, "GPIO 01 (EEFROM SCK)", EPinType.RESERVED),
    29: PinModel(29, 5, "GPIO O5", EPinType.GENERAL),
    30: PinModel(30, None, "Ground", EPinType.GROUND),
    31: PinModel(31, 6, "GPIO O6", EPinType.GENERAL),
    32: PinModel(32, 12, "GPIO 12 (PWM0)", EPinType.PWM),
    33: PinModel(33, 13, "GPIO 13 (PWM1)", EPinType.PWM),
    34: PinModel(34, None, "Ground", EPinType.GROUND),
    35: PinModel(35, 19, "GPIO 19 (PCM FS)", EPinType.PWM),
    36: PinModel(36, 16, "GPIO 16", EPinType.GENERAL),
    37: PinModel(37, 26, "GPIO 26", EPinType.GENERAL),
    38: PinModel(38, 20, "GPIO 20 (PCM DIN)", EPinType.GENERAL),
    39: PinModel(39, None, "Ground", EPinType.GROUND),
    40: PinModel(40, 21, "GPIO 21 (PCM DOUT)", EPinType.GENERAL),
}