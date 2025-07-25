from _ast import Raise
from typing import Dict, List

from common.converters import motor_converter
from common.converters.motor_converter import motor_model_to_dto
from db.model.motor_model import MotorModel
from db.model.db_config import db_obj
from db.model.pin_model import PinModel
from dto.pin_dto import PinDto
from services.pin_service import get_pin
from servomotor.controller import ControllerPWM
from servomotor.common import MotorStatus
from dto.motor_dto import MotorDto
import asyncio
from services import pin_service
import threading

# Fixed services slots (IDs 1–4)
controller_pool: Dict[int, ControllerPWM] = {}
controller_lock = threading.Lock()

def update_controller(motor_dto: MotorDto):
    current_controller = get_controller(motor_dto.id)

    with controller_lock:
        if current_controller.status == MotorStatus.RUNNING:
            raise ValueError("Motor is already running")
        current_controller.target_freq = motor_dto.target_freq
        current_controller.duty = motor_dto.duty
        current_controller.start_freq = motor_dto.start_freq
        current_controller.accel_steps = motor_dto.accel_steps
        current_controller.decel_steps = motor_dto.decel_steps
        current_controller.total_steps = motor_dto.total_steps

def get_controller(motor_id: int) -> ControllerPWM | None:
    with controller_lock:
        controller = controller_pool.get(motor_id)

        if controller:
            return controller

        motor_model = get_motor(motor_id)
        if motor_model is None:
            return None

        controller = ControllerPWM(
            pi=pin_service.pi,
            pin_enable=motor_model.pin_enable.pigpio_pin_number,
            pin_forward=motor_model.pin_forward.pigpio_pin_number,
            pin_step=motor_model.pin_step.pigpio_pin_number,
            total_steps=motor_model.total_steps,
            target_freq=int(motor_model.target_freq),
            duty=motor_model.duty,
            start_freq=int(motor_model.start_freq),
            accel_steps=motor_model.accel_steps,
            decel_steps=motor_model.decel_steps
        )
        controller_pool[motor_id] = controller
        return controller

def get_all() -> list[MotorDto]:
    motor_models = MotorModel.query.all()
    return [motor_model_to_dto(motor_model) for motor_model in motor_models]

def get_motor(motor_id: int) -> MotorDto | None:
    motor_model = MotorModel.query.get(motor_id)
    return motor_model_to_dto(motor_model) if motor_model else None

def get_motor_status(motor_id: int) -> str:
    controller = get_controller(motor_id)
    return controller.status.value if controller else "not_configured"

def run_motor(motor_id: int, forward: bool = True) -> bool:
    controller = get_controller(motor_id)

    if controller:
        controller.run(forward=forward) # asyncio.create_task()
        return True
    return False

def stop_motor(motor_id: int) -> bool:
    controller = get_controller(motor_id)
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
        update_controller(motor_dto)

        return motor_dto

