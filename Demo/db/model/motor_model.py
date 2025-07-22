
from db.model.db_config import db_obj
from db.model.device_model import DeviceModel

class MotorModel(DeviceModel):
    __tablename__ = 'motors'

    id = db_obj.Column(db_obj.Integer, db_obj.ForeignKey('devices.id'), primary_key=True)
    pin_step_id = db_obj.Column(db_obj.Integer, db_obj.ForeignKey('pins.id'))
    pin_forward_id = db_obj.Column(db_obj.Integer, db_obj.ForeignKey('pins.id'))
    pin_enable_id = db_obj.Column(db_obj.Integer, db_obj.ForeignKey('pins.id'))

    start_freq = db_obj.Column(db_obj.Float, nullable=False)
    target_freq = db_obj.Column(db_obj.Float, nullable=False)
    angle = db_obj.Column(db_obj.Float, nullable=False)
    duty = db_obj.Column(db_obj.Float, nullable=False)
    accel_steps = db_obj.Column(db_obj.Integer, nullable=True, default=0)
    decel_steps = db_obj.Column(db_obj.Integer, nullable=True, default=0)
    loops = db_obj.Column(db_obj.Float, default=1)

    pin_step = db_obj.relationship("PinModel", foreign_keys=[pin_step_id])
    pin_forward = db_obj.relationship("PinModel", foreign_keys=[pin_forward_id])
    pin_enable = db_obj.relationship("PinModel", foreign_keys=[pin_enable_id])

    __mapper_args__ = {
        'polymorphic_identity': 'services'
    }
