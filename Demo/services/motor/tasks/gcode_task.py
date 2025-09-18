import threading
import traceback
from enum import Enum
from typing import Unpack, Optional

from flask_socketio import SocketIO
from gcodeparser import GcodeParser, GcodeLine

from common import utils
from core.event.event_dispatcher import EventDispatcher
from db.dao.motor_dao import MotorDao
from db.model.motor_model import MotorModel
from event.motor_task_event import TaskGcodeFinishedEvent, TaskOriginFinishedEvent, SingleMotorTaskEvent, TaskStepFinishedEvent
from event.pin_status_change_event import PinStatusChangeEvent
from services.controller.controller_protocol import ControllerProtocol
from services.motor.tasks.base_run_task import BaseMotorTask
from services.motor.tasks.move_origin_task import MoveOriginTask
from services.motor.tasks.move_steps_task import MoveStepsTask
from services.motor.tasks.run_task_protocol import ExecKwargs, SingleMotorTaskProtocol
from collections import deque

from servomotor.controller_status import EMotorStatus
from servomotor.event.controller_event import MotorStatusData


class EGcodeCommand(str, Enum):
    G0 = "G0"

class EMotorLabel(str, Enum):
    X = "X"
    Y = "Y"
    Z = "Z"

    @classmethod
    def from_value(cls, value: str, default: "EMotorLabel" = None) -> Optional["EMotorLabel"]:
        try:
            return cls(value)
        except ValueError:
            return default

class GcodeTask(BaseMotorTask):
    def __init__(self,
                 controller_service: ControllerProtocol,
                 dispatcher: EventDispatcher,
                 socketio: SocketIO,
                 motor_dao: MotorDao,
                 motor_x_id: int,
                 motor_y_id: int,
                 motor_z_id: int,
                 gcode_cmd: str):
        super().__init__(controller_service, dispatcher)

        self._socketio = socketio
        self.__motor_dao = motor_dao

        self.__gcode_lines = deque(GcodeParser(gcode_cmd).lines)
        self.__current_line: Optional[GcodeLine] = None

        self.__execute_kwargs = {}

        self.__tasks: dict[EMotorLabel, SingleMotorTaskProtocol] = {}
        self.__motor_ids = {
            EMotorLabel.X: motor_x_id,
            EMotorLabel.Y: motor_y_id,
            EMotorLabel.Z: motor_z_id,
        }

    @property
    def current_line(self) -> Optional[GcodeLine]:
        return self.__current_line

    def move_to_next_line(self) -> Optional[GcodeLine]:
        self.__current_line = self.__gcode_lines.popleft() if self.__gcode_lines else None
        return self.__current_line

    def handle_controller_status_change(self, event: MotorStatusData):
        for task in self.__tasks.values():
            task.handle_controller_status_change(event)

        if (self.is_finished is False) and event.status == EMotorStatus.STOPPED:
            self._start_all_tasks()

    def handle_pin_status_change(self, event: PinStatusChangeEvent):
        for task in self.__tasks.values():
            task.handle_pin_status_change(event)

    def execute(self, **kwargs: Unpack[ExecKwargs]) -> None:
        self._is_finished = False
        self.__execute_kwargs = kwargs

        self._start_all_tasks()

    def stop(self):
        self._is_finished = True

        for task in self.__tasks.values():
            task.stop()

    def _start_all_tasks(self):
        if self._controller_service.is_any_controller_running():
            print("All controllers must be stopped before starting new gcode task.")
            return

        command_line = self.move_to_next_line()
        if command_line is None:
            print("No more gcode lines to execute.")
            self.stop()
            self._dispatcher.emit_async(TaskGcodeFinishedEvent(task_id=self.uuid))
            return

        print(f"Starting all controllers for gcode task: {self.current_line}")

        empty_cmd = True
        for label_str, distance in command_line.params.items():
            # Search which motor X, Y or Z is associated with the param, continue to next param if not valid X, Y or Z found
            label = EMotorLabel.from_value(label_str)
            if label is None or distance is None:
                continue

            # Load motor from DB, continue to next param if not found
            motor = self.__motor_dao.get_by_id(self.__motor_ids[label])
            if motor is None:
                continue

            # If distance is 0 create an origin task
            if distance == 0:
                # check if the motor is already at origin
                if motor.position == motor.origin:
                    continue
                task = MoveOriginTask(controller_service=self._controller_service, dispatcher=self._dispatcher, motor=motor)
            else:
                # Create an step task

                # Convert distance to steps, if steps are 0 continue to next param
                steps = utils.calculate_motor_total_steps(motor.angle, abs(distance), motor.distance_per_turn)
                if steps <= 0:
                    continue

                # Determine motion direction
                direction = motor.clockwise if distance > 0 else not motor.clockwise
                task = MoveStepsTask(controller_service=self._controller_service, dispatcher=self._dispatcher, motor=motor, steps=steps, direction=direction)

            print(f"Starting task: {distance} for motor: {motor.id}")
            self.__tasks[label] = task
            self._socketio.start_background_task(self._start_task, motor, label)
            empty_cmd = False

        if empty_cmd:
            print(f"No motors to move for command line: {self.current_line}")
            self._start_all_tasks()

    def _start_task(self, motor: MotorModel, label: EMotorLabel):
        try:
            self.__tasks[label].execute(**self.__execute_kwargs)
        except Exception as e:
            traceback.print_exc()
            self.stop()
            self._dispatcher.emit_async(TaskGcodeFinishedEvent(task_id=self.uuid, error=e, motor=motor))
            raise e