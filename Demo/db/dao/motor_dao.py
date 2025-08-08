from db.model.motor_model import MotorModel
from db.dao.pin_dao import PinDao
from flask_sqlalchemy import SQLAlchemy

class MotorDao:
    def __init__(self, db: SQLAlchemy, pin_dao: PinDao):
        self.__db = db
        self.__pin_dao = pin_dao

    @staticmethod
    def get_by_id(motor_id: int) -> MotorModel:
        return MotorModel.query.get(motor_id)

    @staticmethod
    def get_all() -> list[MotorModel]:
        return MotorModel.query.all()

    def update_motor(self, motor_model: MotorModel) -> MotorModel:
        with self.__db.session.begin():
            self.__db.session.merge(motor_model)
            return motor_model

    def seed_default_motors(self):
        if MotorModel.query.count() > 0:
            print("[Motor Seed] Motors already exist. Skipping.")
            return

        self.__pin_dao.seed_default_pins()

        print("[Motor Seed] Creating default motors...")
        motor_configs = [
            {
                "id": 1,
                "name": "Motor 1",
                "step": 12,
                "dir": 16,
                "enable": 26
            },
            {
                "id": 2,
                "name": "Motor 2",
                "step": 13,
                "dir": 17,
                "enable": 13
            },
            {
                "id": 3,
                "name": "Motor 3",
                "step": 18,
                "dir": 22,
                "enable": 23
            },
            {
                "id": 4,
                "name": "Motor 4",
                "step": 19,
                "dir": 24,
                "enable": 25
            },
        ]
        for cfg in motor_configs:
            pin_step = self.__pin_dao.find_pin_by_gpio_number(cfg["step"])
            pin_forward = self.__pin_dao.find_pin_by_gpio_number(cfg["dir"])
            pin_enable = self.__pin_dao.find_pin_by_gpio_number(cfg["enable"])

            # Mark pins as used
            pin_step.in_use = True
            pin_forward.in_use = True
            pin_enable.in_use = True

            motor = MotorModel(
                id=cfg["id"],
                name=cfg["name"],
                pin_step=pin_step,
                pin_forward=pin_forward,
                pin_enable=pin_enable,
                target_freq=300,
                angle=1.8,
                duty=50,
                turns=1
            )
            self.__db.session.add(motor)

        self.__db.session.commit()
        print("[Motors] Default motors inserted.")