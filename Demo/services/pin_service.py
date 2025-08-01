from typing import Optional
from db.dao.pin_dao import PinDao
from dto.motor_dto import MotorDto
from dto.pin_dto import PinDto
from common.converters.pin_converter import pin_model_to_dto
from db.model.motor_model import MotorModel

class PinService:
    @staticmethod
    def get_all() -> list[PinDto]:
        pin_models = PinDao.get_all()
        return [pin_model_to_dto(pin) for pin in pin_models]

    @staticmethod
    def get_available_pins() -> list[PinDto]:
        pin_models = PinDao.get_available_pins()
        return [pin_model_to_dto(pin) for pin in pin_models]

    @staticmethod
    def get_used_pins() -> list[PinDto]:
        pin_models = PinDao.get_used_pins()
        return [pin_model_to_dto(pin) for pin in pin_models]

    @staticmethod
    def get_pin(pin_id: int) -> Optional[PinDto]:
        pin = PinDao.get_by_id(pin_id)
        return pin_model_to_dto(pin) if pin else None

    @staticmethod
    def is_pin_available(pin_id: int) -> bool:
        pin = PinService.get_pin(pin_id)
        return pin and not pin.in_use

    @staticmethod
    def are_pins_available(pin_ids: list[int]) -> bool:
        pins = PinDao.get_many_by_ids(pin_ids=pin_ids)
        return pins and pin_ids.__len__() == pins.__len__() and all(p and not p.in_use for p in pins)

    @staticmethod
    def is_pin_config_valid(motor_dto: MotorDto, motor_model: MotorModel) -> bool:
        pins_to_check = []
        if motor_dto.pin_step and motor_dto.pin_step.id != motor_model.pin_step_id:
            pins_to_check.append(motor_dto.pin_step.id)
        if motor_dto.pin_forward and motor_dto.pin_forward.id != motor_model.pin_forward_id:
            pins_to_check.append(motor_dto.pin_forward.id)
        if motor_dto.pin_enable and motor_dto.pin_enable.id != motor_model.pin_enable_id:
            pins_to_check.append(motor_dto.pin_enable.id)

        return PinService.are_pins_available(pins_to_check)











# def set_pin_in_use(pin_id: int, in_use: bool = False):
#     pin_model = PinModel.query.get(pin_id)
#     if pin_model:
#         if in_use:
#             available = is_pin_available(pin_id)
#             if not available:
#                 raise ValueError(f"Pin {pin_id} is already in use.")
#         pin_model.in_use = in_use
#         db_obj.session.commit()
#
# def set_pins_in_use(pins: list[int], in_use: bool = False):
#     try:
#         with db_obj.session.begin():
#             for pin_id in pins:
#                 pin_model = PinModel.query.get(pin_id)
#                 if not pin_model:
#                     raise ValueError(f"Pin {pin_id} not found.")
#
#                 if in_use:
#                     available = is_pin_available(pin_id)
#                     if not available:
#                         raise ValueError(f"Pin {pin_id} is already in use.")
#                 pin_model.in_use = in_use
#     except (SQLAlchemyError, ValueError) as e:
#         db_obj.session.rollback()
#         raise e
#
# def replace_pin_in_use(pin_old_id: int, pin_new_id: int):
#     try:
#         with db_obj.session.begin():
#             pin_old_model = PinModel.query.get(pin_old_id)
#
#             if not pin_old_model:
#                 raise ValueError("One or both pins not found")
#
#             if pin_old_id == pin_new_id:
#                 pin_old_model.in_use = True
#             else:
#                 pin_new_model = PinModel.query.get(pin_new_id)
#
#                 if not pin_new_model:
#                     raise ValueError("One or both pins not found")
#
#                 pin_old_model.in_use = False
#                 pin_new_model.in_use = True
#
#     except (SQLAlchemyError, ValueError) as e:
#         db_obj.session.rollback()
#         raise e