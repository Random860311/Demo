from typing import Optional

from flask import Flask

from db.dao.base_dao import BaseDao, DatabaseDao
from db.model.motor_model import MotorModel
from db.dao.pin_dao import PinDao
from flask_sqlalchemy import SQLAlchemy

from dto.motor_dto import MotorDto


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
                    motor.home = motor.position
                    motor.position = 0
                return motors

    def set_origin_all(self) -> list[MotorModel]:
        with self._app.app_context():
            with self._db.session.begin_nested():
                motors = MotorModel.query.all()
                for motor in motors:
                    motor.origin = motor.position
                return motors

    @staticmethod
    def to_model(dto: MotorDto, motor_model: MotorModel):
        motor_model.name = dto.name if dto.name else f"Motor {dto.id}"
        motor_model.target_freq = dto.target_freq
        motor_model.angle = dto.angle
        motor_model.duty = dto.duty
        motor_model.distance_per_turn = dto.distance_per_turn
        motor_model.position = dto.position
        motor_model.home = dto.home
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
                "step": 32,
                "dir": 36,
                "enable": 37
            },
            {
                "id": 2,
                "name": "Motor 2",
                "step": 33,
                "dir": 11,
                "enable": 13
            },
            {
                "id": 3,
                "name": "Motor 3",
                "step": 12,
                "dir": 15,
                "enable": 16
            },
            {
                "id": 4,
                "name": "Motor 4",
                "step": 35,
                "dir": 18,
                "enable": 22
            },
        ]
        for cfg in motor_configs:
            pin_step = self.__pin_dao.get_by_id(cfg["step"])
            pin_forward = self.__pin_dao.get_by_id(cfg["dir"])
            pin_enable = self.__pin_dao.get_by_id(cfg["enable"])

            motor = MotorModel(
                id=cfg["id"],
                name=cfg["name"],
                pin_step_id =pin_step.id,
                pin_forward_id=pin_forward.id,
                pin_enable_id=pin_enable.id,
                target_freq=300,
                angle=1.8,
                duty=50,
                turns=1,
                position=0,
            )
            self._db.session.add(motor)

        self._db.session.commit()
        print("[Motors] Default motors inserted.")