import pigpio

from dto.motor_dto import MotorDto
from . import motor_service
# from db.model.motor_model import MotorModel
from servomotor.controller import ControllerPWM
from servomotor.controller_status import MotorStatus
from typing import Dict
import threading

pi = pigpio.pi()  # shared pigpio connection

# Fixed services slots (IDs 1–4)
controller_pool: Dict[int, ControllerPWM] = {}
controller_lock = threading.Lock()

def get_pi() -> pigpio.pi:
    global pi
    if pi is None or not pi.connected:
        pi = pigpio.pi()
    return pi

def get_controller(motor_id: int) -> ControllerPWM | None:
    with controller_lock:
        controller = controller_pool.get(motor_id)

        if controller:
            if not controller.pi or not controller.pi.connected:
                controller.pi = get_pi()
                controller_pool[motor_id] = controller
            return controller

        motor_dto = motor_service.get_motor(motor_id)
        if motor_dto is None:
            return None

        controller = ControllerPWM(
            pi=get_pi(),
            pin_enable=motor_dto.pin_enable.pigpio_pin_number,
            pin_forward=motor_dto.pin_forward.pigpio_pin_number,
            pin_step=motor_dto.pin_step.pigpio_pin_number,
            total_steps=motor_dto.total_steps,
            target_freq=int(motor_dto.target_freq),
            duty=motor_dto.duty,
            start_freq=int(motor_dto.start_freq),
            accel_steps=motor_dto.accel_steps,
            decel_steps=motor_dto.decel_steps
        )
        controller_pool[motor_id] = controller
        return controller

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