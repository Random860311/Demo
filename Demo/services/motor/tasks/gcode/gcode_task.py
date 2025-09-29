import traceback
from typing import Unpack, Optional

from flask_socketio import SocketIO
from gcodeparser import GcodeLine

from common import utils
from core.event.event_dispatcher import EventDispatcher
from db.dao.motor_dao import MotorDao
from db.model.motor.motor_label import EMotorLabel
from db.model.motor.motor_model import MotorModel
from event.motor_event import TaskGcodeFinishedEvent
from event.pin_event import PinStatusChangeEvent
from services.controller.controller_protocol import ControllerServiceProtocol
from services.motor.tasks.base_task import BaseMotorTask
from services.motor.tasks.gcode.gcode_command import EGcodeCommand
from services.motor.tasks.gcode.gcode_converter import parse_gcode_cmd
from services.motor.tasks.origin.origin_task import MoveOriginTask
from services.motor.tasks.steps.steps_task import MoveStepsTask
from services.motor.tasks.task_protocol import ExecKwargs, SingleMotorTaskProtocol
from collections import deque

from servomotor.dto.controller_status import EMotorStatus

class GcodeTask(BaseMotorTask):
    def __init__(self,
                 controller_service: ControllerServiceProtocol,
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

        self.__gcode_lines = deque(parse_gcode_cmd(gcode_cmd)) #deque(GcodeParser(gcode_cmd).lines)
        # print(f"Gcode task: {GcodeParser(gcode_cmd).lines}")

        for lines in self.__gcode_lines:
            print(lines.gcode_str)
        self.__current_line: Optional[GcodeLine] = None

        self.__tasks: dict[EMotorLabel, SingleMotorTaskProtocol] = {}
        self.__motor_ids = {
            EMotorLabel.X: motor_x_id,
            EMotorLabel.Y: motor_y_id,
            EMotorLabel.Z: motor_z_id,
        }

    @property
    def controller_ids(self) -> list[int]:
        return list(self.__motor_ids.values())

    @property
    def current_line(self) -> Optional[GcodeLine]:
        return self.__current_line

    def move_to_next_line(self) -> Optional[GcodeLine]:
        self.__current_line = self.__gcode_lines.popleft() if self.__gcode_lines else None
        return self.__current_line

    def handle_controller_status_change(self, event: MotorEvent):
        for task in self.__tasks.values():
            task.handle_controller_status_change(event)

        if (self.is_finished is False) and event.status == EMotorStatus.STOPPED:
            self._start_all_tasks()

    def handle_pin_status_change(self, event: PinStatusChangeEvent):
        for task in self.__tasks.values():
            task.handle_pin_status_change(event)

    def execute(self, **kwargs: Unpack[ExecKwargs]) -> None:
        super().execute(**kwargs)
        self._start_all_tasks()

    def stop(self):
        self._is_finished = True

        for task in self.__tasks.values():
            task.stop()

    def _start_all_tasks(self):
        if self._controller_service.is_any_running():
            # print("All controllers must be stopped before starting new gcode task.")
            return

        command_line = self.move_to_next_line()
        if command_line is None:
            print("No more gcode lines to execute.")
            self.stop()
            self._dispatcher.emit_async(TaskGcodeFinishedEvent(task_id=self.uuid))
            return

        empty_cmd = True

        for label_str, distance in command_line.params.items():
            # Parse label and command
            label = EMotorLabel.from_value(label_str)
            command = EGcodeCommand.from_value(command_line.command_str)
            if (label is None) or (command is None) or (distance is None):
                continue

            # Load motor from DB, continue to next param if not found
            motor = self.__motor_dao.get_by_id(self.__motor_ids[label])
            if motor is None:
                continue

            freq_hz = 0
            match command:
                case EGcodeCommand.G0:
                    freq_hz = motor.fast_freq
                case EGcodeCommand.G1:
                    freq_hz = motor.target_freq
            # print(f"Gcode freq: {freq_hz}")
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

            print(f"Starting task with distance: {distance} for motor: {motor.id}")
            self.__tasks[label] = task
            self._socketio.start_background_task(self._start_task, motor, label, freq_hz)
            empty_cmd = False

        if empty_cmd:
            print(f"No motors to move for command line: {self.current_line}")
            self._start_all_tasks()

    def _start_task(self, motor: MotorModel, label: EMotorLabel, freq_hz: int):
        try:
            self.__tasks[label].execute(**dict(self._execute_kwargs, freq_hz=freq_hz))
        except Exception as e:
            traceback.print_exc()
            self.stop()
            self._dispatcher.emit_async(TaskGcodeFinishedEvent(task_id=self.uuid, error=e, motor=motor))
            raise e