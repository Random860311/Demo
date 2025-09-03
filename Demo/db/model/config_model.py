from db.model.db_config import db_app

class ConfigModel(db_app.Model):
    __tablename__ = 'configs'

    id = db_app.Column(db_app.Integer, primary_key=True)
    value_x = db_app.Column(db_app.Float, nullable=True)
    value_y = db_app.Column(db_app.Float, nullable=True)
    value_z = db_app.Column(db_app.Float, nullable=True)

