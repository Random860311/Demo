from db.model.db_config import db_app


class DeviceModel(db_app.Model):
    __tablename__ = 'devices'

    id = db_app.Column(db_app.Integer, primary_key=True)
    name = db_app.Column(db_app.String(50), nullable=False)
    type = db_app.Column(db_app.String(50))  # for polymorphic identity

    __mapper_args__ = {
        'polymorphic_identity': 'device',
        'polymorphic_on': type
    }
