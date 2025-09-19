import traceback
from typing import Optional

from flask_socketio import SocketIO

from core.event.event_dispatcher import EventDispatcher
from db.dao.motor_dao import MotorDao
from db.model.motor.motor_model import MotorModel
from error.app_warning import AppWarning
from event.motor_task_event import TaskHomeFinishedEvent, TaskStepFinishedEvent, TaskOriginFinishedEvent, SingleMotorTaskEvent, TaskGcodeFinishedEvent
from event.pin_status_change_event import PinStatusChangeEvent

from services.controller.controller_protocol import ControllerProtocol
from services.motor.motor_protocol import MotorServiceProtocol
from services.motor.tasks.gcode.gcode_task import GcodeTask
from services.motor.tasks.origin.origin_task import MoveOriginTask
from services.motor.tasks.task_protocol import SingleMotorTaskProtocol, MotorTaskProtocol
from services.motor.tasks.home.home_task import FindHomeTask
from services.motor.tasks.steps.steps_task import MoveStepsTask
from services.pigpio.pigpio_protocol import PigpioProtocol
from services.pin.pin_protocol import pin_model_to_dto

from servomotor.controller_status import EMotorStatus
from servomotor.event.controller_event import MotorStatusData
from web.events.motor_event import MotorUpdatedEvent, MotorCalibrationChangedEvent

from dto.motor_dto import MotorDto

from services.base_service import BaseService


class MotorService(BaseService, MotorServiceProtocol):

    def __init__(self, dispatcher: EventDispatcher, socketio: SocketIO, pigpio: PigpioProtocol, controller_service: ControllerProtocol, motor_dao: MotorDao):
        super().__init__(dispatcher, socketio)

        self.__pigpio_service = pigpio
        self.__controller_service = controller_service
        self.__motor_dao = motor_dao

        self.__calibration_enabled = False

        self.__single_tasks: dict[int, SingleMotorTaskProtocol] = {}
        self.__multy_tasks: Optional[MotorTaskProtocol] = None

        self._subscribe_to_events()

    def is_calibration_enabled(self)-> bool:
        return self.__calibration_enabled

    def set_calibration(self, value: bool) -> bool:
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
            dto = self.__to_dto(motor_model)
            # dto.status = self.get_motor_status(motor_model.id)
            motor_dtos.append(dto)

        return motor_dtos

    def get_motor(self, motor_id: int) -> Optional[MotorDto]:
        motor_model = self.__motor_dao.get_by_id(motor_id)
        return  self.__to_dto(motor_model) if motor_model else None

    def update_motor(self, motor_dto: MotorDto) -> MotorDto:
        if self.__controller_service.is_controller_running(motor_dto.id):
            raise ValueError(f"Cannot update motor '{motor_dto.name}' when it is still running.")

        existing_motor_model = self.__motor_dao.get_by_id(motor_dto.id)
        MotorDao.to_model(motor_dto, existing_motor_model)

        updated_model = self.__motor_dao.update_motor(existing_motor_model)
        updated_dto = self.__to_dto(updated_model)

        self.__controller_service.update_controller(updated_dto)
        self._dispatcher.emit_async(MotorUpdatedEvent(updated_dto))

        return updated_dto

    def __set_home(self, motor_id: int):
        model = self.__motor_dao.set_home(motor_id)
        self.__controller_service.set_controller_home(motor_id)

        dto = self.__to_dto(model)
        self._dispatcher.emit_async(MotorUpdatedEvent(dto))

    def set_origin_all(self):
        if self.__controller_service.is_any_controller_running():
            raise ValueError("Cannot set origin to all motors when some motors are still running.")

        models = self.__motor_dao.set_origin_all()
        for model in models:
            dto = self.__to_dto(model)
            self._dispatcher.emit_async(MotorUpdatedEvent(dto))

    def set_origin(self, motor_id: int):
        if self.__controller_service.is_controller_running(motor_id):
            raise ValueError("Cannot set origin while motor is still running.")

        model = self.__motor_dao.set_origin(motor_id)
        dto = self.__to_dto(model)
        self._dispatcher.emit_async(MotorUpdatedEvent(dto))

    def set_limit_all(self):
        if self.__controller_service.is_any_controller_running():
            raise ValueError("Cannot set origin to all motors when some motors are still running.")

        models = self.__motor_dao.set_limit_all()
        for model in models:
            dto = self.__to_dto(model)
            self._dispatcher.emit_async(MotorUpdatedEvent(dto))

    def set_limit(self, motor_id: int):
        if self.__controller_service.is_controller_running(motor_id):
            raise ValueError("Cannot set origin while motor is still running.")

        model = self.__motor_dao.set_limit(motor_id)
        dto = self.__to_dto(model)
        self._dispatcher.emit_async(MotorUpdatedEvent(dto))

    def get_motor_status(self, motor_id: int) -> EMotorStatus:
        return self.__controller_service.get_controller_status(motor_id)

    def move_to_home(self, motor_id: int):
        motor_model = self.__motor_dao.get_by_id(motor_id)

        config = MotorDao.get_pin_config(motor_model.id)

        self.run(FindHomeTask(controller_service=self.__controller_service,
                              dispatcher=self._dispatcher,
                              socketio=self._socketio,
                              gpio_service=self.__pigpio_service,
                              motor=motor_model,
                              home_pin_id=config.home.id))

    def move_to_origin(self, motor_id: int):
        motor_model = self.__motor_dao.get_by_id(motor_id)

        self.run(MoveOriginTask(controller_service=self.__controller_service,
                                dispatcher=self._dispatcher,
                                motor=motor_model))

    def move_steps(self, motor_id: int, steps: int = 1, forward: bool = True):
        motor_model = self.__motor_dao.get_by_id(motor_id)
        print(f"Move steps: {steps} forward: {forward}")
        self.run(MoveStepsTask(controller_service=self.__controller_service,
                               motor=motor_model,
                               dispatcher=self._dispatcher,
                               steps=steps,
                               direction=forward))

    def run_gcode(self, gcode: str):
        self.run(GcodeTask(controller_service = self.__controller_service,
                                       dispatcher = self._dispatcher,
                                       socketio = self._socketio,
                                       motor_dao = self.__motor_dao,
                                       gcode_cmd = gcode,
                                       motor_x_id = 1,
                                       motor_y_id = 2,
                                       motor_z_id = 3))

    def run(self, task: MotorTaskProtocol):
        try:
            if self.__multy_tasks and self.__multy_tasks.is_finished:
                raise AppWarning("Cannot run a motor when a task that involve multiple motors is already running. Stop the current task before starting a new one.")

            if isinstance(task, SingleMotorTaskProtocol):
                current_task = self.__single_tasks.get(task.controller_id, None)
                if current_task and not current_task.is_finished:
                    raise AppWarning("Cannot run a motor when a task is already running. Stop the current task before starting a new one.")

                self.__single_tasks[task.controller_id] = task
            else:
                self.__multy_tasks = task

            task.execute(pass_limits=self.__calibration_enabled)
        except AppWarning as ew:
            self.stop_motor(task.controller_id if isinstance(task, SingleMotorTaskProtocol) else None)
            self._dispatcher.emit_async(ew)
        except Exception as e:
            print(f"Error in MotorService run: {e}")
            traceback.print_exc()
            self.stop_motor(task.controller_id if isinstance(task, SingleMotorTaskProtocol) else None)

    def stop_motor(self, motor_id: Optional[int] = None) -> bool:
        if motor_id:
            current_task = self.__single_tasks.get(motor_id, None)
            if current_task:
                current_task.stop()
                del self.__single_tasks[motor_id]

            return self.__controller_service.stop_controller(motor_id)
        elif self.__multy_tasks:
            self.__multy_tasks.stop()
            self.__multy_tasks = None
            self.__controller_service.stop_all_controllers()
        return True

    def _handle_controller_status_change(self, event: MotorStatusData):
        motor_model = self.__motor_dao.get_by_id(event.motor_id)

        motor_dto = self.__to_dto(motor_model)
        motor_dto.status = event.status
        motor_dto.position = event.position

        try:
            self.__motor_dao.update_motor_position(event.motor_id, event.position)
            current_task = self.__single_tasks.get(event.motor_id, None)
            if current_task and current_task.is_finished is False:
                current_task.handle_controller_status_change(event)

            if self.__multy_tasks:
                self.__multy_tasks.handle_controller_status_change(event)
        except AppWarning as ew:
            self.stop_motor(event.motor_id)
            self._dispatcher.emit_async(ew)
            motor_dto.status = EMotorStatus.STOPPED
        except Exception as e:
            traceback.print_exc()
            self.stop_motor(event.motor_id)
            motor_dto.status = EMotorStatus.STOPPED
        finally:
            self._dispatcher.emit_async(MotorUpdatedEvent(motor_dto))

    def _handle_single_motor_task_finished_event(self, event: SingleMotorTaskEvent):
        if isinstance(event, TaskHomeFinishedEvent):
            self.__set_home(event.motor_id)

        current_task = self.__single_tasks.get(event.motor_id, None)
        if current_task and current_task.uuid == event.task_id:
            self.stop_motor(event.motor_id)

    def _handle_multy_task_finished_event(self, event: TaskGcodeFinishedEvent):
        self.stop_motor()
        self.__multy_tasks = None

        if event.error:
            if isinstance(event.error, AppWarning):
                self._dispatcher.emit_async(event.error)
            else:
                self._dispatcher.emit_async(AppWarning("Error in motor task."))

    def _handle_pin_event(self, event: PinStatusChangeEvent):
        for task in self.__single_tasks.values():
            task.handle_pin_status_change(event)

        if self.__multy_tasks:
            self.__multy_tasks.handle_pin_status_change(event)

    def _subscribe_to_events(self):
        self._dispatcher.subscribe(MotorStatusData, self._handle_controller_status_change)
        self._dispatcher.subscribe(PinStatusChangeEvent, self._handle_pin_event)

        self._dispatcher.subscribe(TaskHomeFinishedEvent, self._handle_single_motor_task_finished_event)
        self._dispatcher.subscribe(TaskStepFinishedEvent, self._handle_single_motor_task_finished_event)
        self._dispatcher.subscribe(TaskOriginFinishedEvent, self._handle_single_motor_task_finished_event)

        self._dispatcher.subscribe(TaskGcodeFinishedEvent, self._handle_multy_task_finished_event)

    def __to_dto(self, motor_model: MotorModel) -> MotorDto:
        pin_config = MotorDao.get_pin_config(motor_model.id)

        motor_dto = MotorDto(
            id=motor_model.id,
            name=motor_model.name,

            pin_step=pin_model_to_dto(pin_config.steps),
            pin_forward=pin_model_to_dto(pin_config.dir),
            pin_enable=pin_model_to_dto(pin_config.enable),
            pin_home=pin_model_to_dto(pin_config.home),

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