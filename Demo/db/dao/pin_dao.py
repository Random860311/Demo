from typing import Optional

from flask_sqlalchemy import SQLAlchemy

from db.model.pin_model import PinModel, PIN_MAP


class PinDao:
    @staticmethod
    def get_all() -> list[PinModel]:
        return list(PIN_MAP.values())

    @staticmethod
    def get_by_id(pin_id: int) -> Optional[PinModel]:
        return PIN_MAP.get(pin_id, None)

    @staticmethod
    def get_by_gpio_number(number: int) -> Optional[PinModel]:
        return next((p for p in PIN_MAP.values() if p.pigpio_pin_number == number), None)

    @staticmethod
    def get_by_physical_number(number: int) -> Optional[PinModel]:
        return PinDao.get_by_id(number)