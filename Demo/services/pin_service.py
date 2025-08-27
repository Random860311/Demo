from typing import Optional
from db.dao.pin_dao import PinDao
from dto.pin_dto import PinDto
from common.converters.pin_converter import pin_model_to_dto

class PinService:
    @staticmethod
    def get_all() -> list[PinDto]:
        pin_models = PinDao.get_all()
        return [pin_model_to_dto(pin) for pin in pin_models]

    @staticmethod
    def get_pin(pin_id: int) -> Optional[PinDto]:
        pin = PinDao.get_by_id(pin_id)
        return pin_model_to_dto(pin) if pin else None

