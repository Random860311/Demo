from _ast import Raise
from typing import Dict, List

from common.converters import motor_converter
from common.converters.motor_converter import motor_model_to_dto
from db.model.motor_model import MotorModel
from db.model.db_config import db_obj
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
            decel_steps=motor_model.decel_steps,
            loops=motor_model.loops
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

def update_motor(motor: MotorDto):
    motor_model = MotorModel.query.get(motor.id)

    if not pin_service.are_pins_available([motor_model.pin_step_id, motor_model.pin_forward_id, motor_model.pin_enable_id]):
        raise RuntimeError("Not enough pins available for services ID {motor.id}")

    motor_model = motor_converter.apply_motor_dto_to_model(motor_model, motor)

    #pin_service.set_pins_in_use([motor_model.pin_step_id, motor_model.pin_forward_id, motor_model.pin_enable_id], True)

    current_controller = get_controller(motor.id)
    current_controller.pin_forward = motor_model.pin_forward.pigpio_pin_number
    current_controller.pin_step = motor_model.pin_step.pigpio_pin_number
    current_controller.pin_enable = motor_model.pin_enable.pigpio_pin_number

    db_obj.session.commit()


