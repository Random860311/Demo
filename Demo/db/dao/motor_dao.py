from typing import Optional

from flask import Flask

from db.dao.base_dao import BaseDao, DatabaseDao
from db.model.motor_model import MotorModel, MotorPinConfig
from db.dao.pin_dao import PinDao
from flask_sqlalchemy import SQLAlchemy

from dto.motor_dto import MotorDto

PINS_CONFIG = [
    MotorPinConfig(
        motor_id=1,
        steps=PinDao.get_by_id(32),
        dir=PinDao.get_by_id(36),
        enable=PinDao.get_by_id(37),
        home=PinDao.get_by_id(16)
    ),
    MotorPinConfig(
        motor_id=2,
        steps=PinDao.get_by_id(33),
        dir=PinDao.get_by_id(11),
        enable=PinDao.get_by_id(13),
        home=PinDao.get_by_id(22)
    ),
    MotorPinConfig(
        motor_id=3,
        steps=PinDao.get_by_id(35),
        dir=PinDao.get_by_id(18),
        enable=PinDao.get_by_id(26),
        home=PinDao.get_by_id(29)
    ),
]

class MotorDao(DatabaseDao[MotorModel]):
    def __init__(self,app: Flask, db: SQLAlchemy, pin_dao: PinDao):
        super().__init__(app, db)
        self.__pin_dao = pin_dao

    def get_by_id(self, obj_id: int) -> Optional[MotorModel]:
        with self._app.app_context():
            return MotorModel.query.get(obj_id)

    def get_all(self) -> list[MotorModel]:
        with self._app.app_context():
            return MotorModel.query.all()

    def update_motor_position(self, motor_id: int, steps: int) -> None:
        with self._app.app_context():
            with self._db.session.begin_nested():
                motor = MotorModel.query.get(motor_id)
                motor.position = steps

    def get_motor_position(self, motor_id: int) -> int:
        with self._app.app_context():
            motor = MotorModel.query.get(motor_id)
            return motor.position

    def update_motor(self, motor_model: MotorModel) -> MotorModel:
        with self._app.app_context():
            with self._db.session.begin_nested():
                self._db.session.merge(motor_model)
                return motor_model

    def set_home_all(self) -> list[MotorModel]:
        with self._app.app_context():
            with self._db.session.begin_nested():
                motors = MotorModel.query.all()
                for motor in motors:
                    motor.position = 0
                return motors

    def set_home(self, motor_id: int) -> MotorModel:
        with self._app.app_context():
            with self._db.session.begin_nested():
                motor = MotorModel.query.get(motor_id)
                motor.position = 0

                return motor

    def set_origin_all(self) -> list[MotorModel]:
        with self._app.app_context():
            with self._db.session.begin_nested():
                motors = MotorModel.query.all()
                for motor in motors:
                    motor.origin = motor.position
                return motors

    def set_origin(self, motor_id: int) -> MotorModel:
        with self._app.app_context():
            with self._db.session.begin_nested():
                motor = MotorModel.query.get(motor_id)
                motor.origin = motor.position
                return motor

    def set_limit_all(self) -> list[MotorModel]:
        with self._app.app_context():
            with self._db.session.begin_nested():
                motors = MotorModel.query.all()
                for motor in motors:
                    motor.limit = motor.position
                return motors

    def set_limit(self, motor_id: int) -> MotorModel:
        with self._app.app_context():
            with self._db.session.begin_nested():
                motor = MotorModel.query.get(motor_id)
                motor.limit = motor.position
                return motor

    @staticmethod
    def get_pin_config(motor_id: int) -> MotorPinConfig:
        return PINS_CONFIG[motor_id - 1]

    @staticmethod
    def get_all_pin_configs() -> list[MotorPinConfig]:
        return PINS_CONFIG

    @staticmethod
    def to_model(dto: MotorDto, motor_model: MotorModel):
        motor_model.name = dto.name if dto.name else f"Motor {dto.id}"
        motor_model.target_freq = dto.target_freq
        motor_model.angle = dto.angle
        motor_model.duty = dto.duty
        motor_model.distance_per_turn = dto.distance_per_turn
        motor_model.position = dto.position
        motor_model.origin = dto.origin

        return motor_model

    def seed_default_motors(self):
        if MotorModel.query.count() > 0:
            print("[Motor Seed] Motors already exist. Skipping.")
            return

        print("[Motor Seed] Creating default motors...")
        motor_configs = [
            {
                "id": 1,
                "name": "Motor 1",
            },
            {
                "id": 2,
                "name": "Motor 2",
            },
            {
                "id": 3,
                "name": "Motor 3",
            },
        ]
        for cfg in motor_configs:
            motor = MotorModel(
                id=cfg["id"],
                name=cfg["name"],
                target_freq=300,
                angle=1.8,
                duty=50,
                turns=1,
                position=0,
            )
            self._db.session.add(motor)

        self._db.session.commit()
        print("[Motors] Default motors inserted.")