from dataclasses import dataclass
from typing import Optional

from db.model.db_config import db_app
from db.model.device_model import DeviceModel
from db.model.pin_model import PinModel, PIN_MAP


class MotorModel(DeviceModel):
    __tablename__ = 'motors'

    id = db_app.Column(db_app.Integer, db_app.ForeignKey('devices.id'), primary_key=True)

    target_freq = db_app.Column(db_app.Float, nullable=False)
    angle = db_app.Column(db_app.Float, nullable=False)
    duty = db_app.Column(db_app.Float, nullable=False)
    distance_per_turn = db_app.Column(db_app.Float, default=0, nullable=False)

    # Current position, measured in steps from home
    position = db_app.Column(db_app.Integer, default=0)

    # Origin position
    origin = db_app.Column(db_app.Integer, nullable=True)

    # Home position
    # home = db_app.Column(db_app.Integer, nullable=True)

    # Max number of steps from home (always a positive number)
    limit = db_app.Column(db_app.Integer, nullable=True)

    clockwise = db_app.Column(db_app.Boolean, nullable=False, default=True)

    __mapper_args__ = {
        'polymorphic_identity': 'services'
    }

@dataclass
class MotorPinConfig:
    motor_id: int
    steps: PinModel
    dir: PinModel
    enable: PinModel
    home: PinModel