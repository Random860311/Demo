import flask.app
from flask_sqlalchemy import SQLAlchemy
from web import app

init_done = False

db_obj = SQLAlchemy()
#db_obj.init_app(app.app)


def initialize():
    from db.dao import pin_dao, motor_dao

    global init_done

    if not init_done:
        print("Creating tables...")
        with app.app.app_context():
            db_obj.create_all()
            pin_dao.seed_default_pins()
            motor_dao.seed_default_motors()

            init_done = True

