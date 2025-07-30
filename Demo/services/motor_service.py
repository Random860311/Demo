
from . import pigpio_service
from common.converters import motor_converter
from common.converters.motor_converter import motor_model_to_dto
from db.model.motor_model import MotorModel
from db.model.db_config import db_obj

from dto.motor_dto import MotorDto
from services import pin_service

def get_all() -> list[MotorDto]:
    motor_models = MotorModel.query.all()
    return [motor_model_to_dto(motor_model) for motor_model in motor_models]

def get_motor(motor_id: int) -> MotorDto | None:
    motor_model = MotorModel.query.get(motor_id)
    return motor_model_to_dto(motor_model) if motor_model else None

def get_motor_status(motor_id: int) -> str:
    controller = pigpio_service.get_controller(motor_id)
    return controller.status if controller else "not_configured"

def run_motor(motor_id: int, forward: bool = True, infinite: bool = False) -> bool:
    controller = pigpio_service.get_controller(motor_id)

    if controller:
        controller.run(forward=forward, infinite=infinite) # asyncio.create_task()
        return True
    return False

def stop_motor(motor_id: int) -> bool:
    controller = pigpio_service.get_controller(motor_id)
    if controller:
        controller.stop()
        return True
    return False

def update_motor(motor_dto: MotorDto) -> MotorDto:
    """
    Update motor controller and db configuration, this method does not update pins configuration
    :param motor_dto: new motor configuration
    :return: The new configuration
    """
    with db_obj.session.begin():
        existing_motor_model = MotorModel.query.get(motor_dto.id)
        motor_converter.motor_dto_to_model(motor_dto, existing_motor_model)
        pigpio_service.update_controller(motor_dto)

        return motor_dto

