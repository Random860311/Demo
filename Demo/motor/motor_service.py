from typing import Dict, List
from servomotor.controller import ControllerPWM
from servomotor.common import MotorStatus
from dto.motor_config_dto import MotorConfigDto
import asyncio
from motor import pigpio_service

# Fixed motor slots (IDs 1–4)
motor_pool: Dict[int, ControllerPWM] = {}

def get_motor(motor_id: int) -> ControllerPWM | None:
    return motor_pool.get(motor_id)

def get_motor_status(motor_id: int) -> str:
    motor = motor_pool.get(motor_id)
    return motor.status.value if motor else "not_configured"

def run_motor(motor_id: int, forward: bool) -> bool:
    motor = motor_pool.get(motor_id)
    if motor:
        asyncio.create_task(motor.run(forward=forward))
        return True
    return False

def stop_motor(motor_id: int) -> bool:
    motor = motor_pool.get(motor_id)
    if motor:
        asyncio.create_task(motor.stop())
        return True
    return False

def clear_all():
    motor_pool.clear()
    pigpio_service.clear_all_pins()

def configure_all_motors(configs: List[MotorConfigDto]) -> list[str]:
    errors = []
    clear_all()

    if len(configs) > 4:
        raise RuntimeError("Only motor IDs 1 to 4 are supported.")

    for cfg in configs:
        configure_motor(cfg)

    return errors

def configure_motor(cfg: MotorConfigDto):
    if cfg.id not in (1, 2, 3, 4):
        raise RuntimeError("Invalid motor ID. Must be 1 to 4.")

    pins = [cfg.pin_step, cfg.pin_forward, cfg.pin_enable]

    if not pigpio_service.register_pins(pins):
        raise RuntimeError("One or more GPIO pins already in use.")

    motor_pool[cfg.id] = ControllerPWM(
        pi=pigpio_service.pi,
        total_steps=cfg.total_steps,
        target_freq=cfg.target_freq,
        pin_step=cfg.pin_step,
        pin_forward=cfg.pin_forward,
        pin_enable=cfg.pin_enable,
        duty=cfg.duty,
        start_freq=cfg.start_freq,
        accel_steps=cfg.accel_steps,
        decel_steps=cfg.decel_steps,
        loops=cfg.loops
    )