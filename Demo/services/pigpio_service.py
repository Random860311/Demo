import pigpio

from db.dao.motor_dao import MotorDao
from dto.motor_dto import MotorDto
from common import utils
from servomotor.controller import ControllerPWM
from servomotor.controller_status import MotorStatus
from typing import Dict
import threading

class PigpioService:
    def __init__(self):
        self.__pi = pigpio.pi()
        self._controller_pool: Dict[int, ControllerPWM] = {}
        self._lock = threading.Lock()

    def get_pi(self) -> pigpio.pi:
        if not self.__pi.connected:
            print("Reconnecting pigpio...")
            self.__pi = pigpio.pi()
        return self.__pi

    def get_controller(self, motor_id: int) -> ControllerPWM:
        with self._lock:
            controller = self._controller_pool.get(motor_id)
            if not controller:
                print(f"Creating controller for motor {motor_id}")
                motor_model = MotorDao.get_by_id(motor_id)
                total_turns = utils.calculate_motor_total_turns(motor_model.turns, motor_model.distance, motor_model.distance_per_turn)
                total_steps = utils.calculate_motor_total_steps(motor_model.angle, total_turns)

                controller = ControllerPWM(
                    pi=self.get_pi(),
                    controller_id=motor_id,
                    pin_enable= -1 if not motor_model.pin_enable else motor_model.pin_enable.pigpio_pin_number,
                    pin_forward= -1 if not motor_model.pin_forward else motor_model.pin_forward.pigpio_pin_number,
                    pin_step= -1 if not motor_model.pin_step else motor_model.pin_step.pigpio_pin_number,
                    total_steps=total_steps,
                    target_freq=int(motor_model.target_freq),
                    duty=motor_model.duty,
                )
                self._controller_pool[motor_id] = controller

            if not controller.pi or not controller.pi.connected:
                print(f"Reconnecting pigpio in controller {motor_id}")
                controller.pi = self.get_pi()
            return controller

    def update_controller(self, motor_dto: MotorDto) -> ControllerPWM:
        controller = self.get_controller(motor_dto.id)
        if controller.status == MotorStatus.RUNNING:
            raise ValueError(f"Motor {motor_dto.id} is already running, cannot update.")
        with self._lock:
            controller.pin_enable = -1 if not motor_dto.pin_enable else motor_dto.pin_enable.pigpio_pin_number
            controller.pin_forward = -1 if not motor_dto.pin_forward else motor_dto.pin_forward.pigpio_pin_number
            controller.pin_step = -1 if not motor_dto.pin_step else motor_dto.pin_step.pigpio_pin_number
            controller.target_freq = motor_dto.target_freq
            controller.duty = motor_dto.duty
            controller.total_steps = motor_dto.total_steps
            controller.target_freq = motor_dto.target_freq
            controller.duty = motor_dto.duty
        return controller

# pi = pigpio.pi()  # shared pigpio connection
#
# # Fixed services slots (IDs 1–4)
# controller_pool: Dict[int, ControllerPWM] = {}
# controller_lock = threading.Lock()
#
# def get_pi() -> pigpio.pi:
#     global pi
#     if pi is None or not pi.connected:
#         pi = pigpio.pi()
#     return pi
#
# def get_controller(motor_id: int) -> ControllerPWM | None:
#     with controller_lock:
#         controller = controller_pool.get(motor_id)
#
#         if controller:
#             if not controller.pi or not controller.pi.connected:
#                 controller.pi = get_pi()
#                 controller_pool[motor_id] = controller
#             return controller
#
#         motor_dto = motor_service.get_motor(motor_id)
#         if motor_dto is None:
#             return None
#
#         controller = ControllerPWM(
#             pi=get_pi(),
#             pin_enable=motor_dto.pin_enable.pigpio_pin_number,
#             pin_forward=motor_dto.pin_forward.pigpio_pin_number,
#             pin_step=motor_dto.pin_step.pigpio_pin_number,
#             total_steps=motor_dto.total_steps,
#             target_freq=int(motor_dto.target_freq),
#             duty=motor_dto.duty,
#             start_freq=int(motor_dto.start_freq),
#             accel_steps=motor_dto.accel_steps,
#             decel_steps=motor_dto.decel_steps
#         )
#         controller_pool[motor_id] = controller
#         return controller
#
# def update_controller(motor_dto: MotorDto):
#     current_controller = get_controller(motor_dto.id)
#
#     with controller_lock:
#         if current_controller.status == MotorStatus.RUNNING:
#             raise ValueError("Motor is already running")
#         current_controller.target_freq = motor_dto.target_freq
#         current_controller.duty = motor_dto.duty
#         current_controller.start_freq = motor_dto.start_freq
#         current_controller.accel_steps = motor_dto.accel_steps
#         current_controller.decel_steps = motor_dto.decel_steps
#         current_controller.total_steps = motor_dto.total_steps