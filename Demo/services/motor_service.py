from typing import Optional
from core.event.event_dispatcher import EventDispatcher
from db.dao.motor_dao import MotorDao
from db.model.motor_model import MotorModel
from error.app_warning import AppWarning
from servomotor.controller_run_mode import EControllerRunMode
from servomotor.controller_status import EMotorStatus
from servomotor.event.controller_event import MotorStatusData
from web.events.motor_event import MotorUpdatedEvent, MotorCalibrationChangedEvent
from common import utils
from dto.motor_dto import MotorDto
from web.events.pin_event import PinStatusEvent
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

        self.__calibration_enabled = False

        self._subscribe_to_events()

    def is_calibration_enabled(self)-> bool:
        """
        Determines if the calibration mode is enabled.

        Checks the state of the calibration mode and returns whether it is
        enabled or not.

        :return: True if calibration mode is enabled, False otherwise.
        :rtype: bool
        """
        return self.__calibration_enabled

    def set_calibration(self, value: bool) -> bool:
        """
        Sets the calibration state for the system. This method determines if calibration
        is to be enabled or disabled. It ensures that calibration cannot be toggled while
        any motor controllers are actively running. Returns whether the calibration state
        was changed successfully.

        :param value: The desired calibration state. `True` to enable calibration,
            `False` to disable.
        :return: `True` if the calibration state was changed, `False` if the requested
            state matches the current state.

        :raises ValueError: If calibration is attempted while any motor controllers
            are still running.
        """
        if self.__calibration_enabled == value:
            return False
        if self.__controller_service.is_any_controller_running():
            raise ValueError("Cannot set calibration while some motors are still running.")

        self.__calibration_enabled = value

        self._dispatcher.emit_async(MotorCalibrationChangedEvent(value))
        return True

    def get_all(self) -> list[MotorDto]:
        motor_models = self.__motor_dao.get_all()
        motor_dtos: list[MotorDto]= []

        for motor_model in motor_models:
            dto = self.to_dto(motor_model)
            # dto.status = self.get_motor_status(motor_model.id)
            motor_dtos.append(dto)

        return motor_dtos

    def get_motor(self, motor_id: int) -> Optional[MotorDto]:
        motor_model = self.__motor_dao.get_by_id(motor_id)
        return  self.to_dto(motor_model) if motor_model else None

    def set_home_all(self):
        if self.__controller_service.is_any_controller_running():
            raise ValueError("Cannot set home to all motors when some motors are still running.")

        models = self.__motor_dao.set_home_all()
        self.__controller_service.set_all_controllers_home()

        for model in models:
            dto = self.to_dto(model)
            self._dispatcher.emit_async(MotorUpdatedEvent(dto))

    def set_home(self, motor_id: int):
        if self.__controller_service.is_controller_running(motor_id):
            raise ValueError("Cannot set home while motor is still running.")

        model = self.__motor_dao.set_home(motor_id)
        self.__controller_service.set_controller_home(motor_id)

        dto = self.to_dto(model)
        self._dispatcher.emit_async(MotorUpdatedEvent(dto))

    def set_origin_all(self):
        if self.__controller_service.is_any_controller_running():
            raise ValueError("Cannot set origin to all motors when some motors are still running.")

        models = self.__motor_dao.set_origin_all()
        for model in models:
            dto = self.to_dto(model)
            self._dispatcher.emit_async(MotorUpdatedEvent(dto))

    def set_origin(self, motor_id: int):
        if self.__controller_service.is_controller_running(motor_id):
            raise ValueError("Cannot set origin while motor is still running.")

        model = self.__motor_dao.set_origin(motor_id)
        dto = self.to_dto(model)
        self._dispatcher.emit_async(MotorUpdatedEvent(dto))

    def set_limit_all(self):
        if self.__controller_service.is_any_controller_running():
            raise ValueError("Cannot set origin to all motors when some motors are still running.")

        models = self.__motor_dao.set_limit_all()
        for model in models:
            dto = self.to_dto(model)
            self._dispatcher.emit_async(MotorUpdatedEvent(dto))

    def set_limit(self, motor_id: int):

        if self.__controller_service.is_controller_running(motor_id):
            raise ValueError("Cannot set origin while motor is still running.")

        model = self.__motor_dao.set_limit(motor_id)
        dto = self.to_dto(model)
        self._dispatcher.emit_async(MotorUpdatedEvent(dto))

    def get_motor_status(self, motor_id: int) -> EMotorStatus:
        return self.__controller_service.get_controller_status(motor_id)

    def move_to_home(self, motor_id: int):
        model = self.__motor_dao.get_by_id(motor_id)
        self.__move_to_home(model)

    def move_to_home_all(self):
        models = self.__motor_dao.get_all()
        for model in models:
            self.__move_to_home(model)

    def move_to_origin(self, motor_id: int):
        model = self.__motor_dao.get_by_id(motor_id)
        self.__move_to_origin(model)

    def move_to_origin_all(self):
        models = self.__motor_dao.get_all()
        for model in models:
            self.__move_to_origin(model)

    def __move_to_home(self, motor_model: MotorModel):
        if motor_model.position == 0:
            return

        if self.__controller_service.is_controller_running(motor_model.id):
            raise ValueError(f"Cannot move to home to motor {motor_model.id} when it is still running.")

        direction_forward = not motor_model.clockwise
        run_steps = abs(motor_model.position)

        print(f"move_to_home: {motor_model.id} forward: {direction_forward} stepsize: {run_steps} position: {motor_model.position}")
        self.__run_motor(motor_model, run_steps, forward=direction_forward)
        print("Finished move_to_home")

    def __move_to_origin(self, motor_model: MotorModel):
        if motor_model.origin == motor_model.position:
            return

        if self.__controller_service.is_controller_running(motor_model.id):
            raise ValueError(f"Cannot move to origin to motor {motor_model.id} when it is still running.")

        direction_forward = motor_model.position < motor_model.origin
        run_steps = abs(motor_model.origin - motor_model.position)

        print(f"move_to_origin: {motor_model.id} forward: {direction_forward} stepsize: {run_steps} origin: {motor_model.origin} position: {motor_model.position}")
        self.__run_motor(motor_model.id, run_steps, forward=direction_forward)
        print("Finished move_to_origin")

    def __asert_motor_operation(self,
                                motor: MotorModel,
                                position: int,
                                forward: bool,
                                steps: int = 0):

        end_position = position + (steps if forward else -steps)

        print(f"__asert_motor_operation: {motor.id} forward: {forward} steps: {steps} position: {position} end_position: {end_position} limit: {motor.limit}")

        # Check that motor has valid origin
        if not self.__calibration_enabled and not motor.origin:
            raise AppWarning(f"Motor {motor.id} does not have origin set.")

        # Check that motor has valid limit
        if not self.__calibration_enabled and not motor.limit:
            raise AppWarning(f"Motor {motor.id} does not have limit set.")

        # Check if clockwise motor is at home
        if motor.clockwise and not forward and end_position <= 0:
            raise AppWarning(f"Motor {motor.id} is at home and can't continue running in counter-clockwise direction.")

        # Check if counter-clockwise motor is at home
        if not motor.clockwise and forward and end_position >= 0:
            raise AppWarning(f"Motor {motor.id} is at home and can't continue running in clockwise direction.")

        # Check if clockwise motor is at limit
        if (not self.__calibration_enabled) and motor.clockwise and forward and end_position >= motor.limit:
            raise AppWarning(f"Motor {motor.id} is at limit  and can't continue running in clockwise direction.")

        # Check if counter-clockwise motor is at limit
        if (not self.__calibration_enabled) and (not motor.clockwise) and (not forward) and end_position <= motor.limit:
            raise AppWarning(f"Motor {motor.id} is at limit and can't continue running in counter-clockwise direction.")

    def run_motor(self, motor_id: int, run_mode: EControllerRunMode = EControllerRunMode.SINGLE_STEP, distance: Optional[float] = None, forward: bool = True):
        motor_model = self.__motor_dao.get_by_id(motor_id)

        run_steps: Optional[int] = None
        match run_mode:
            case EControllerRunMode.SINGLE_STEP:
                run_steps = 1
            case EControllerRunMode.INFINITE:
                run_steps = 0
            case EControllerRunMode.CONFIG:
                run_steps = utils.calculate_motor_total_steps(motor_angle=motor_model.angle, distance=distance, distance_per_turn=motor_model.distance_per_turn)

        assert run_steps is not None
        self.__run_motor(motor_model, run_steps, forward=forward)

    def __run_motor(self, model: MotorModel, steps: int, forward: bool = True):
        self.__asert_motor_operation(motor=model, position=model.position, forward=forward, steps=steps)

        controller = self.__controller_service.get_controller(model.id)
        controller.run(forward=forward, steps=steps)

    def stop_motor(self, motor_id: int):
        controller = self.__controller_service.get_controller(motor_id)
        controller.stop()

    def update_motor(self, motor_dto: MotorDto) -> MotorDto:
        existing_motor_model = self.__motor_dao.get_by_id(motor_dto.id)
        MotorDao.to_model(motor_dto, existing_motor_model)

        updated_model = self.__motor_dao.update_motor(existing_motor_model)
        updated_dto = self.to_dto(updated_model)

        self.__controller_service.update_controller(updated_dto)
        self._dispatcher.emit_async(MotorUpdatedEvent(updated_dto))

        print(f"MotorService update_motor: {motor_dto.id}, {motor_dto.position}")
        return updated_dto

    def _handle_controller_status_change(self, event: MotorStatusData):
        motor_model = self.__motor_dao.get_by_id(event.motor_id)

        motor_dto = self.to_dto(motor_model)

        try:
            motor_dto.status = event.status
            motor_dto.position = event.position

            self.__motor_dao.update_motor_position(event.motor_id, event.position)
            if event.status == EMotorStatus.RUNNING:
                self.__asert_motor_operation(motor=motor_model, position=event.position, forward=event.forward)
        except AppWarning as ew:
            self._dispatcher.emit_async(ew)
            self.stop_motor(event.motor_id)
        except Exception as e:
            print(f"Error in MotorService _handle_controller_status_change: {e}")
            self.stop_motor(event.motor_id)
        finally:
            self._dispatcher.emit_async(MotorUpdatedEvent(motor_dto))

    def _handle_pin_status_change(self, event: PinStatusEvent):
        pass

    def _subscribe_to_events(self):
        self._dispatcher.subscribe(MotorStatusData, self._handle_controller_status_change)
        self._dispatcher.subscribe(PinStatusEvent, self._handle_pin_status_change)

    def to_dto(self, motor_model: MotorModel) -> MotorDto:
        pin_config = MotorDao.get_pin_config(motor_model.id)

        motor_dto = MotorDto(
            id=motor_model.id,
            name=motor_model.name,

            pin_step=PinService.to_dto(pin_config.steps),
            pin_forward=PinService.to_dto(pin_config.dir),
            pin_enable=PinService.to_dto(pin_config.enable),
            pin_home=PinService.to_dto(pin_config.home),

            angle=motor_model.angle,
            target_freq=motor_model.target_freq,
            duty=motor_model.duty,
            distance_per_turn=motor_model.distance_per_turn,

            position=motor_model.position,
            origin=motor_model.origin,
            limit=motor_model.limit,

            status=self.get_motor_status(motor_model.id),
        )

        return motor_dto

