import threading
import traceback
from typing import Optional

from flask_socketio import SocketIO

from core.event.event_dispatcher import EventDispatcher
from db.dao.motor_dao import MotorDao
from db.model.motor.motor_model import MotorModel
from error.app_warning import AppWarning
from event.motor_event import TaskHomeFinishedEvent, TaskStepFinishedEvent, TaskOriginFinishedEvent, SingleMotorTaskEvent, TaskGcodeFinishedEvent, TaskEvent
from event.pin_event import PinStatusChangeEvent

from services.controller.controller_protocol import ControllerServiceProtocol
from services.motor.motor_protocol import MotorServiceProtocol
from services.motor.tasks.gcode.gcode_task import GcodeTask
from services.motor.tasks.origin.origin_task import MoveOriginTask
from services.motor.tasks.task_protocol import MotorTaskProtocol
from services.motor.tasks.home.home_task import FindHomeTask
from services.motor.tasks.steps.steps_task import MoveStepsTask
from services.pigpio.pigpio_protocol import PigpioProtocol
from services.pin.pin_protocol import pin_model_to_dto
from servomotor.dto.controller_status import EMotorStatus
from servomotor.event.controller_event import ControllerStatusEvent, ControllerPositionEvent
from web.events.motor_event import MotorUpdatedEvent, CalibrationChangedEvent

from dto.motor_dto import MotorDto

from services.base_service import BaseService


class MotorService(BaseService, MotorServiceProtocol):

    def __init__(self, dispatcher: EventDispatcher, socketio: SocketIO, pigpio: PigpioProtocol, controller_service: ControllerServiceProtocol, motor_dao: MotorDao):
        super().__init__(dispatcher, socketio)

        self.__pigpio_service = pigpio
        self.__controller_service = controller_service
        self.__motor_dao = motor_dao

        self.__calibration_enabled = False

        self.__tasks: list[MotorTaskProtocol] = []
        self.__tasks_lock = threading.RLock()

        self._subscribe_to_events()

    def is_calibration_enabled(self)-> bool:
        return self.__calibration_enabled

    def set_calibration(self, value: bool) -> bool:
        if self.__calibration_enabled == value:
            return False
        if self.__controller_service.is_any_running():
            raise ValueError("Cannot set calibration while some motors are still running.")

        self.__calibration_enabled = value

        self._dispatcher.emit_async(CalibrationChangedEvent(value))
        return True

    def get_all(self) -> list[MotorDto]:
        motor_models = self.__motor_dao.get_all()
        motor_dtos: list[MotorDto]= []

        for motor_model in motor_models:
            dto = self.__to_dto(motor_model)
            # dto.status = self.get_motor_status(motor_model.id)
            motor_dtos.append(dto)

        return motor_dtos

    def get_by_id(self, motor_id: int) -> Optional[MotorDto]:
        motor_model = self.__motor_dao.get_by_id(motor_id)
        return  self.__to_dto(motor_model) if motor_model else None

    def update(self, motor_dto: MotorDto) -> MotorDto:
        if self.__controller_service.is_running(motor_dto.id):
            raise ValueError(f"Cannot update motor '{motor_dto.name}' when it is still running.")

        updated_model = self.__motor_dao.update_motor(motor_dto)
        updated_dto = self.__to_dto(updated_model)

        self.__emit_updated_motor_event(motor=updated_dto)

        return updated_dto

    def set_origin_all(self):
        if self.__controller_service.is_any_running():
            raise ValueError("Cannot set origin to all motors when some motors are still running.")

        models = self.__motor_dao.set_origin_all()
        for model in models:
            dto = self.__to_dto(model)
            self.__emit_updated_motor_event(motor=dto)

    def set_limit_all(self):
        if self.__controller_service.is_any_running():
            raise ValueError("Cannot set origin to all motors when some motors are still running.")

        models = self.__motor_dao.set_limit_all()
        for model in models:
            dto = self.__to_dto(model)
            self.__emit_updated_motor_event(motor=dto)

    def set_origin(self, motor_id: int):
        if self.__controller_service.is_running(motor_id):
            raise ValueError("Cannot set origin while motor is still running.")

        model = self.__motor_dao.set_origin(motor_id)
        dto = self.__to_dto(model)
        self.__emit_updated_motor_event(motor=dto)

    def set_limit(self, motor_id: int):
        if self.__controller_service.is_running(motor_id):
            raise ValueError("Cannot set origin while motor is still running.")

        model = self.__motor_dao.set_limit(motor_id)
        dto = self.__to_dto(model)
        self.__emit_updated_motor_event(motor=dto)

    def run_to_home(self, motor_id: int):
        motor_model = self.__motor_dao.get_by_id(motor_id)
        config = self.__motor_dao.get_pin_config(motor_model.id)

        self.run(FindHomeTask(
            controller_service=self.__controller_service,
            dispatcher=self._dispatcher,
            socketio=self._socketio,
            gpio_service=self.__pigpio_service,
            motor=motor_model,
            home_pin_id=config.home.id)
        )

    def run_to_origin(self, motor_id: int):
        motor_model = self.__motor_dao.get_by_id(motor_id)
        self.run(MoveOriginTask(controller_service=self.__controller_service,
                                dispatcher=self._dispatcher,
                                motor=motor_model))

    def run_steps(self, motor_id: int, steps: int = 1, forward: bool = True):
        motor_model = self.__motor_dao.get_by_id(motor_id)
        self.run(MoveStepsTask(controller_service=self.__controller_service,
                               motor=motor_model,
                               dispatcher=self._dispatcher,
                               steps=steps,
                               direction=forward))

    def run_gcode(self, gcode: str):
        task = GcodeTask(controller_service = self.__controller_service,
                         dispatcher = self._dispatcher,
                         socketio = self._socketio,
                         motor_dao = self.__motor_dao,
                         gcode_cmd = gcode,
                         motor_x_id = 1,
                         motor_y_id = 2,
                         motor_z_id = 3)
        self.run(task)

    def run(self, task: MotorTaskProtocol):
        try:
            with self.__tasks_lock:
                for motor_id in task.controller_ids:
                    if self.__controller_service.is_running(motor_id):
                        raise AppWarning(f"Cannot run motor '{motor_id}' when it is still running.")
                    for existing_task in self.__tasks:
                        if (not existing_task.is_finished) and (motor_id in existing_task.controller_ids):
                            raise AppWarning(f"Cannot run motor '{motor_id}' when there are other tasks running.")

                self.__tasks.append(task)
            task.execute(pass_limits=self.__calibration_enabled)
        except AppWarning as ew:
            self.stop(task.controller_ids)
            self._dispatcher.emit_async(ew)
        except Exception as e:
            print(f"Error in MotorService run: {e}")
            traceback.print_exc()
            self.stop(task.controller_ids)

    def stop(self, ids: list[int]) -> None:
        with self.__tasks_lock:
            for cid in ids:
                for task in self.__tasks:
                    if cid in task.controller_ids:
                        task.stop()

    def __clean_tasks(self):
        with self.__tasks_lock:
            self.__tasks[:] = [t for t in self.__tasks if not t.is_finished]

    def _handle_controller_position_change(self, event: ControllerPositionEvent):
        self.__motor_dao.update_motor_position(event.motor_id, event.position)

        self.__emit_updated_motor_id_event(motor_id=event.motor_id, position=event.position)

    def __handle_controller_status_change(self, event: ControllerStatusEvent):
        if event.status == EMotorStatus.STOPPED:
            self.__clean_tasks()
        self.__emit_updated_motor_id_event(motor_id=event.motor_id, status=event.status)

    def __handle_home_task_finished(self, event: TaskHomeFinishedEvent):
        self.__controller_service.set_home(event.motor_id)
        self.__clean_tasks()
        self.__check_task_error(event)

    def __handle_step_task_finished_event(self, event: TaskStepFinishedEvent):
        self.__clean_tasks()
        self.__check_task_error(event)

    def __handle_origin_task_finished_event(self, event: TaskOriginFinishedEvent):
        self.__clean_tasks()
        self.__check_task_error(event)

    def __handle_gcode_task_finished_event(self, event: TaskGcodeFinishedEvent):
        self.__clean_tasks()
        self.__check_task_error(event)

    def __check_task_error(self, event: TaskEvent):
        if event.error:
            if isinstance(event.error, AppWarning):
                self._dispatcher.emit_async(event.error)
            else:
                self._dispatcher.emit_async(AppWarning("Error in motor task."))

    def _subscribe_to_events(self):
        self._dispatcher.subscribe(ControllerStatusEvent, self.__handle_controller_status_change)

        self._dispatcher.subscribe(TaskHomeFinishedEvent, self.__handle_home_task_finished)
        self._dispatcher.subscribe(TaskStepFinishedEvent, self.__handle_step_task_finished_event)
        self._dispatcher.subscribe(TaskOriginFinishedEvent, self.__handle_origin_task_finished_event)
        self._dispatcher.subscribe(TaskGcodeFinishedEvent, self.__handle_gcode_task_finished_event)

    @staticmethod
    def __to_dto(motor_model: MotorModel) -> MotorDto:
        motor_dto = MotorDto(
            id=motor_model.id,
            name=motor_model.name,

            angle=motor_model.angle,
            target_freq=motor_model.target_freq,
            duty=motor_model.duty,
            distance_per_turn=motor_model.distance_per_turn,

            position=motor_model.position,
            origin=motor_model.origin,
            limit=motor_model.limit
        )

        return motor_dto

    def __emit_updated_motor_id_event(self, motor_id: int, position: Optional[int] = None, status: Optional[EMotorStatus] = None):
        model = self.__motor_dao.get_by_id(motor_id)
        dto = self.__to_dto(model)
        self.__emit_updated_motor_event(dto, position, status)

    def __emit_updated_motor_event(self, motor: MotorDto, position: Optional[int] = None, status: Optional[EMotorStatus] = None):
        pin_config = self.__motor_dao.get_pin_config(motor.id)

        motor.pin_step = pin_model_to_dto(pin_config.steps)
        motor.pin_forward = pin_model_to_dto(pin_config.dir)
        motor.pin_enable = pin_model_to_dto(pin_config.enable)
        motor.pin_home = pin_model_to_dto(pin_config.home)

        motor.status = status if status is not None else self.__controller_service.get_status(motor_id=motor.id)
        motor.position = position if position is not None else self.__controller_service.get_position(motor_id=motor.id)

        self._dispatcher.emit_async(MotorUpdatedEvent(motor))