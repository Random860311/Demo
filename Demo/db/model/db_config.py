from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from core.di_container import container


db_app = SQLAlchemy()

init_done = False


def db_initialize():
    from db.dao.motor_dao import MotorDao

    global init_done

    if not init_done:
        print("Creating tables...")
        app = container.resolve_singleton(Flask)

        with app.app_context():

            db_app.create_all()

            motor_dao = container.resolve_singleton(MotorDao)

            motor_dao.seed_default_motors()

            init_done = True

