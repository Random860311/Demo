from typing import Optional
from core.event.event_dispatcher import EventDispatcher
from db.dao.motor_dao import MotorDao
from db.model.motor_model import MotorModel
from servomotor.controller_run_mode import EControllerRunMode
from servomotor.controller_status import EMotorStatus
from servomotor.event.controller_event import MotorStatusData
from web.events.motor_event import MotorUpdatedEvent
from common import utils
from dto.motor_dto import MotorDto
from .base_service import BaseService
from .controller_service import ControllerService
from .pigpio_service import PigpioService
from .pin_service import PinService


class MotorService(BaseService):

    def __init__(self, dispatcher: EventDispatcher, pigpio: PigpioService, controller_service: ControllerService, motor_dao: MotorDao):
        super().__init__(dispatcher)

        self.__pigpio_service = pigpio
        self.__controller_service = controller_service
        self.__motor_dao = motor_dao

        self._subscribe_to_events()

    def get_all(self) -> list[MotorDto]:
        motor_models = self.__motor_dao.get_all()
        motor_dtos: list[MotorDto]= []

        for motor_model in motor_models:
            dto = MotorService.to_dto(motor_model)
            # dto.status = self.get_motor_status(motor_model.id)
            motor_dtos.append(dto)

        return motor_dtos

    def get_motor(self, motor_id: int) -> Optional[MotorDto]:
        motor_model = self.__motor_dao.get_by_id(motor_id)
        motor_dto = MotorService.to_dto(motor_model) if motor_model else None
        motor_dto.status = self.get_motor_status(motor_id)

        return motor_dto

    def set_home_all(self):
        if self.__controller_service.is_any_controller_running():
            raise ValueError("Cannot set home to all motors when some motors are still running.")

        models = self.__motor_dao.set_home_all()
        self.__controller_service.set_all_controllers_home()

        for model in models:
            dto = MotorService.to_dto(model)
            self._dispatcher.emit_async(MotorUpdatedEvent(dto))

    def set_origin_all(self):
        if self.__controller_service.is_any_controller_running():
            raise ValueError("Cannot set origin to all motors when some motors are still running.")

        models = self.__motor_dao.set_origin_all()
        for model in models:
            dto = MotorService.to_dto(model)
            self._dispatcher.emit_async(MotorUpdatedEvent(dto))

    def get_motor_status(self, motor_id: int) -> EMotorStatus:
        return self.__controller_service.get_controller_status(motor_id)

    def move_to_home(self, motor_id: int):
        if self.__controller_service.is_controller_running(motor_id):
            raise ValueError(f"Cannot move to home to motor {motor_id} when it is still running.")
        model = self.__motor_dao.get_by_id(motor_id)
        self.__move_to_home(model)

    def move_to_home_all(self):
        if self.__controller_service.is_any_controller_running():
            raise ValueError("Cannot move to home to all motors when some motors are still running.")

        models = self.__motor_dao.get_all()
        for model in models:
            self.__move_to_home(model)

    def move_to_origin(self, motor_id: int):
        if self.__controller_service.is_controller_running(motor_id):
            raise ValueError(f"Cannot move to origin to motor {motor_id} when it is still running.")
        model = self.__motor_dao.get_by_id(motor_id)
        self.__move_to_origin(model)

    def move_to_origin_all(self):
        if self.__controller_service.is_any_controller_running():
            raise ValueError("Cannot move to origin to all motors when some motors are still running.")

        models = self.__motor_dao.get_all()
        for model in models:
            self.__move_to_origin(model)

    def __move_to_home(self, motor_model: MotorModel):
        if not motor_model.home or motor_model.home == motor_model.position:
            return
        direction_forward = motor_model.position < motor_model.home
        run_steps = abs(motor_model.home - motor_model.position)

        print(f"move_to_home: {motor_model.id} forward: {direction_forward} stepsize: {run_steps} home: {motor_model.home} position: {motor_model.position}")
        self.__run_motor(motor_model, run_steps, forward=direction_forward)
        print("Finished move_to_home")

    def __move_to_origin(self, motor_model: MotorModel):
        if not motor_model.origin or motor_model.origin == motor_model.position:
            return
        direction_forward = motor_model.position < motor_model.origin
        run_steps = abs(motor_model.origin - motor_model.position)

        print(f"move_to_origin: {motor_model.id} forward: {direction_forward} stepsize: {run_steps} origin: {motor_model.origin} position: {motor_model.position}")
        self.__run_motor(motor_model.id, run_steps, forward=direction_forward)
        print("Finished move_to_origin")

    def run_motor(self, motor_id: int, run_mode: EControllerRunMode = EControllerRunMode.SINGLE_STEP, distance: Optional[float] = None, forward: bool = True):
        motor_model = self.__motor_dao.get_by_id(motor_id)

        match run_mode:
            case EControllerRunMode.SINGLE_STEP:
                run_steps = 1
            case EControllerRunMode.INFINITE:
                run_steps = 0
            case EControllerRunMode.CONFIG:
                if not distance:
                    raise ValueError("Distance must be specified when using CONFIG run mode.")
                run_steps = utils.calculate_motor_total_steps(motor_angle=motor_model.angle, distance=distance, distance_per_turn=motor_model.distance_per_turn)

        self.__run_motor(motor_model, run_steps, forward=forward)

    def __run_motor(self, model: MotorModel, steps: int, forward: bool = True):
        if (not model) or (not model.home) or (not model.origin):
            raise ValueError(f"Motor {model.id} does not have home or origin set.")
        if self.__controller_service.is_controller_running(model.id):
            raise ValueError(f"Motor {model.id} is already running.")

        controller = self.__controller_service.get_controller(model.id)
        if controller.status == EMotorStatus.RUNNING:
            raise ValueError(f"Motor {model.id} is already running.")

        controller.run(forward=forward, steps=steps)

    def stop_motor(self, motor_id: int):
        controller = self.__controller_service.get_controller(motor_id)
        controller.stop()

    def update_motor(self, motor_dto: MotorDto) -> MotorDto:
        existing_motor_model = self.__motor_dao.get_by_id(motor_dto.id)
        MotorDao.to_model(motor_dto, existing_motor_model)

        self.__motor_dao.update_motor(existing_motor_model)
        self.__controller_service.update_controller(motor_dto)
        self._dispatcher.emit_async(MotorUpdatedEvent(motor_dto))
        print(f"MotorService update_motor: {motor_dto.id}, {motor_dto.position}")
        return motor_dto

    def _handle_controller_status_change(self, event: MotorStatusData):
        motor_dto = self.get_motor(event.motor_id)
        motor_dto.status = event.status
        motor_dto.position = event.position
        self.__motor_dao.update_motor_position(event.motor_id, event.position)
        self._dispatcher.emit_async(MotorUpdatedEvent(motor_dto))

        print(f"MotorService _handle_controller_status_change: {motor_dto.id}, {motor_dto.position}")

    def _subscribe_to_events(self):
        self._dispatcher.subscribe(MotorStatusData, self._handle_controller_status_change)

    @staticmethod
    def to_dto(motor_model: MotorModel) -> MotorDto:
        motor_dto = MotorDto(
            id=motor_model.id,
            name=motor_model.name,
            pin_step=None,
            pin_forward=None,
            pin_enable=None,
            angle=motor_model.angle,
            target_freq=motor_model.target_freq,
            duty=motor_model.duty,

            distance_per_turn=motor_model.distance_per_turn,
            position=motor_model.position,

        )
        if motor_model.pin_step:
            motor_dto.pin_step = PinService.to_dto(motor_model.pin_step)
        if motor_model.pin_forward:
            motor_dto.pin_forward = PinService.to_dto(motor_model.pin_forward)
        if motor_model.pin_enable:
            motor_dto.pin_enable = PinService.to_dto(motor_model.pin_enable)
        return motor_dto

