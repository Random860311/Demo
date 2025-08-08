from email.policy import default

from db.model.db_config import db_app
from db.model.device_model import DeviceModel

class MotorModel(DeviceModel):
    __tablename__ = 'motors'

    id = db_app.Column(db_app.Integer, db_app.ForeignKey('devices.id'), primary_key=True)
    pin_step_id = db_app.Column(db_app.Integer, db_app.ForeignKey('pins.id'), nullable=True, default=None)
    pin_forward_id = db_app.Column(db_app.Integer, db_app.ForeignKey('pins.id'), nullable=True, default=None)
    pin_enable_id = db_app.Column(db_app.Integer, db_app.ForeignKey('pins.id'), nullable=True, default=None)

    target_freq = db_app.Column(db_app.Float, nullable=False)
    angle = db_app.Column(db_app.Float, nullable=False)
    duty = db_app.Column(db_app.Float, nullable=False)
    turns = db_app.Column(db_app.Float, default=1)
    distance = db_app.Column(db_app.Float, default=0)
    distance_per_turn = db_app.Column(db_app.Float, default=0)

    pin_step = db_app.relationship("PinModel", foreign_keys=[pin_step_id])
    pin_forward = db_app.relationship("PinModel", foreign_keys=[pin_forward_id])
    pin_enable = db_app.relationship("PinModel", foreign_keys=[pin_enable_id])

    __mapper_args__ = {
        'polymorphic_identity': 'services'
    }
