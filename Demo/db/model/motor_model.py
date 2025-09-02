from typing import Optional

from db.model.db_config import db_app
from db.model.device_model import DeviceModel
from db.model.pin_model import PinModel, PIN_MAP


class MotorModel(DeviceModel):
    __tablename__ = 'motors'

    id = db_app.Column(db_app.Integer, db_app.ForeignKey('devices.id'), primary_key=True)
    pin_step_id = db_app.Column(db_app.Integer, nullable=True, default=None)
    pin_forward_id = db_app.Column(db_app.Integer, nullable=True, default=None)
    pin_enable_id = db_app.Column(db_app.Integer, nullable=True, default=None)

    target_freq = db_app.Column(db_app.Float, nullable=False)
    angle = db_app.Column(db_app.Float, nullable=False)
    duty = db_app.Column(db_app.Float, nullable=False)
    turns = db_app.Column(db_app.Float, default=1)
    distance = db_app.Column(db_app.Float, default=0)
    distance_per_turn = db_app.Column(db_app.Float, default=0)

    position = db_app.Column(db_app.Integer, default=0)
    origin = db_app.Column(db_app.Integer, nullable=True)
    home = db_app.Column(db_app.Integer, nullable=True)

    @property
    def pin_step(self) -> Optional[PinModel]:
        return PIN_MAP.get(self.pin_step_id)

    @property
    def pin_forward(self) -> Optional[PinModel]:
        return PIN_MAP.get(self.pin_forward_id)

    @property
    def pin_enable(self) -> Optional[PinModel]:
        return PIN_MAP.get(self.pin_enable_id)

    __mapper_args__ = {
        'polymorphic_identity': 'services'
    }
