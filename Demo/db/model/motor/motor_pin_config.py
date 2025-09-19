from dataclasses import dataclass

from db.model.pin.pin_model import PinModel


@dataclass
class MotorPinConfig:
    motor_id: int
    steps: PinModel
    dir: PinModel
    enable: PinModel
    home: PinModel
