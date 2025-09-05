from db.model.db_config import db_app
from sqlalchemy import event

class ConfigModel(db_app.Model):
    __tablename__ = 'configs'

    id = db_app.Column(db_app.Integer, primary_key=True)
    value_x = db_app.Column(db_app.Float, nullable=True)
    value_y = db_app.Column(db_app.Float, nullable=True)
    value_z = db_app.Column(db_app.Float, nullable=True)


@event.listens_for(ConfigModel, "before_insert", propagate=True)
def normalize_zero_pk(mapper, connection, target):
    if getattr(target, "id", None) == 0:
        target.id = None