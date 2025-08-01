from common.PinType import PinType
from db.model.db_config import db_app


class PinModel(db_app.Model):
    __tablename__ = 'pins'

    id = db_app.Column(db_app.Integer, primary_key=True)
    pigpio_pin_number = db_app.Column(db_app.Integer, nullable=True)
    physical_pin_number = db_app.Column(db_app.Integer, nullable=False, unique=True)
    in_use = db_app.Column(db_app.Boolean, default=False)
    description = db_app.Column(db_app.String(100))
    pin_type = db_app.Column(db_app.Enum(PinType), nullable=False)


PIN_MAP = [
        # physical, bcm, description, pin_type
        (1, None, "3.3V Power", PinType.POWER),
        (2, None, "5V Power", PinType.POWER),
        (3, 2, "SDA1 (GPIO2)", PinType.GENERAL),
        (4, None, "5V Power", PinType.POWER),
        (5, 3, "SCL1 (GPIO3)", PinType.GENERAL),
        (6, None, "Ground", PinType.GROUND),
        (7, 4, "GPIO4", PinType.GENERAL),
        (8, 14, "TXD0 (GPIO14)", PinType.GENERAL),
        (9, None, "Ground", PinType.GROUND),
        (10, 15, "RXD0 (GPIO15)", PinType.GENERAL),
        (11, 17, "GPIO17", PinType.GENERAL),
        (12, 18, "GPIO18 (PCM_CLK)", PinType.PWM),
        (13, 27, "GPIO27", PinType.GENERAL),
        (14, None, "Ground", PinType.GROUND),
        (15, 22, "GPIO22", PinType.GENERAL),
        (16, 23, "GPIO23", PinType.GENERAL),
        (17, None, "3.3V Power", PinType.POWER),
        (18, 24, "GPIO24", PinType.GENERAL),
        (19, 10, "GPIO10 (MOSI)", PinType.GENERAL),
        (20, None, "Ground", PinType.GROUND),
        (21, 9, "GPIO9 (MISO)", PinType.GENERAL),
        (22, 25, "GPIO25", PinType.GENERAL),
        (23, 11, "GPIO11 (SCLK)", PinType.GENERAL),
        (24, 8, "GPIO8 (CE0)", PinType.GENERAL),
        (25, None, "Ground", PinType.GROUND),
        (26, 7, "GPIO7 (CE1)", PinType.GENERAL),
        (27, None, "ID_SD (EEPROM)", PinType.RESERVED),
        (28, None, "ID_SC (EEPROM)", PinType.RESERVED),
        (29, 5, "GPIO5", PinType.GENERAL),
        (30, None, "Ground", PinType.GROUND),
        (31, 6, "GPIO6", PinType.GENERAL),
        (32, 12, "GPIO12", PinType.PWM),
        (33, 13, "GPIO13", PinType.PWM),
        (34, None, "Ground", PinType.GROUND),
        (35, 19, "GPIO19", PinType.PWM),
        (36, 16, "GPIO16", PinType.GENERAL),
        (37, 26, "GPIO26", PinType.GENERAL),
        (38, 20, "GPIO20", PinType.GENERAL),
        (39, None, "Ground", PinType.GROUND),
        (40, 21, "GPIO21", PinType.GENERAL),
    ]