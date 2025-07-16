from db.model.db_config import db_obj

class DeviceModel(db_obj.Model):
    __tablename__ = 'devices'

    id = db_obj.Column(db_obj.Integer, primary_key=True)
    name = db_obj.Column(db_obj.String(50), nullable=False)
    type = db_obj.Column(db_obj.String(50))  # for polymorphic identity

    __mapper_args__ = {
        'polymorphic_identity': 'device',
        'polymorphic_on': type
    }
