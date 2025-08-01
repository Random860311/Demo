from typing import Optional

from flask_sqlalchemy import SQLAlchemy

from db.model.pin_model import PinModel, PIN_MAP


class PinDao:
    def __init__(self, db: SQLAlchemy):
        self.__db = db

    @staticmethod
    def get_all() -> list[PinModel]:
        return PinModel.query.order_by(PinModel.physical_pin_number).all()

    @staticmethod
    def get_by_id(pin_id: int) -> Optional[PinModel]:
        return PinModel.query.get(pin_id)

    @staticmethod
    def get_many_by_ids(pin_ids: list[int]) -> list[PinModel]:
        return PinModel.query.filter(PinModel.id.in_(pin_ids)).order_by(PinModel.physical_pin_number).all()

    def seed_default_pins(self):
        if PinModel.query.count() > 0:
            print("[Pin Seed] Pins already exist. Skipping.")
            return
        print("[Pins] Populating pin table...")
        pins = []
        for physical, bcm, desc, ptype in PIN_MAP:
            pin = PinModel(
                physical_pin_number=physical,
                pigpio_pin_number=bcm,
                description=desc,
                pin_type=ptype,
                in_use=False
            )
            pins.append(pin)
        self.__db.session.add_all(pins)
        self.__db.session.commit()
        print(f"[Pins] Inserted {len(pins)} pins.")

    @staticmethod
    def get_available_pins() -> list[PinModel]:
        return PinModel.query.filter_by(in_use=False).all()

    @staticmethod
    def get_used_pins() -> list[PinModel]:
        return PinModel.query.filter_by(in_use=True).all()

    @staticmethod
    def find_pin_by_gpio_number(number: int) -> PinModel:
        pin = PinModel.query.filter_by(pigpio_pin_number=number).first()
        if not pin:
            raise ValueError(f"GPIO pin {number} not found in DB.")
        return pin

    @staticmethod
    def find_pin_by_physical_number(number: int) -> PinModel:
        pin = PinModel.query.filter_by(physical_pin_number=number).first()
        if not pin:
            raise ValueError(f"Physical pin {number} not found in DB.")
        return pin