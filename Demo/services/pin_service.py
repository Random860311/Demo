import pigpio
from sqlalchemy.exc import SQLAlchemyError

from db.model.pin_model import PinModel
from dto.pin_dto import PinDto
from common.converters.pin_converter import pin_model_to_dto
from db.model.db_config import db_obj

pi = pigpio.pi()  # shared pigpio connection

def is_pin_available(pin_id: int) -> bool:
    pin = get_pin(pin_id)
    return pin and not pin.in_use

def are_pins_available(pin_ids: list[int]) -> bool:
    pins = get_pins(pin_ids)
    return all(p and not p.in_use for p in pins)

def get_used_pins() -> list[PinDto]:
    pin_models = PinModel.query.filter_by(in_use=True).all()
    return [pin_model_to_dto(pin) for pin in pin_models]

def get_pin(pin_id: int) -> PinDto | None:
    pin = PinModel.query.get(pin_id)
    return pin_model_to_dto(pin) if pin else None

def get_pins(pin_ids: list[int]) -> list[PinDto]:
    return PinModel.query.filter(PinModel.id.in_(pin_ids)).all()

def get_all() -> list[PinDto]:
    pin_models = PinModel.query.order_by(PinModel.physical_pin_number).all()
    return [pin_model_to_dto(pin) for pin in pin_models]

def set_pin_in_use(pin_id: int, in_use: bool = False):
    pin_model = PinModel.query.get(pin_id)
    if pin_model:
        if in_use:
            available = is_pin_available(pin_id)
            if not available:
                raise ValueError(f"Pin {pin_id} is already in use.")
        pin_model.in_use = in_use
        db_obj.session.commit()

def set_pins_in_use(pins: list[int], in_use: bool = False):
    try:
        with db_obj.session.begin():
            for pin_id in pins:
                pin_model = PinModel.query.get(pin_id)
                if not pin_model:
                    raise ValueError(f"Pin {pin_id} not found.")

                if in_use:
                    available = is_pin_available(pin_id)
                    if not available:
                        raise ValueError(f"Pin {pin_id} is already in use.")
                pin_model.in_use = in_use
    except (SQLAlchemyError, ValueError) as e:
        db_obj.session.rollback()
        raise e

def replace_pin_in_use(pin_old_id: int, pin_new_id: int):
    try:
        with db_obj.session.begin():
            pin_old_model = PinModel.query.get(pin_old_id)

            if not pin_old_model:
                raise ValueError("One or both pins not found")

            if pin_old_id == pin_new_id:
                pin_old_model.in_use = True
            else:
                pin_new_model = PinModel.query.get(pin_new_id)

                if not pin_new_model:
                    raise ValueError("One or both pins not found")

                pin_old_model.in_use = False
                pin_new_model.in_use = True

    except (SQLAlchemyError, ValueError) as e:
        db_obj.session.rollback()
        raise e