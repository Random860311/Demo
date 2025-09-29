import threading
from typing import Dict, Optional

from flask_socketio import SocketIO

from core.event.event_dispatcher import EventDispatcher
from core.thread_manager import ThreadManagerProtocol
from db.dao.motor_dao import MotorDao
from dto.motor_dto import MotorDto
from services.base_service import BaseService
from services.controller.controller_protocol import ControllerServiceProtocol
from services.pigpio.pigpio_protocol import PigpioProtocol
from servomotor.controller.controller_protocol import ControllerProtocol

from servomotor.controller.single_controller import SinglePWMController
from servomotor.controller.wave_controller import WavePWMController
from servomotor.dto.controller_status import EMotorStatus
from servomotor.dto.run_cmd_dto import ControllerRunDto
from servomotor.event.controller_event import ControllerStatusEvent, ControllerPositionEvent
from servomotor.tracker.position_tracker import PositionTracker


class ControllerService(BaseService, ControllerServiceProtocol):

    def __init__(self, dispatcher: EventDispatcher, socketio: SocketIO, pigpio: PigpioProtocol, motor_dao: MotorDao, thread_manager: ThreadManagerProtocol):
        super().__init__(dispatcher, socketio)

        self.__motor_dao = motor_dao
        self.__pigpio_service = pigpio
        self.__thread_manager = thread_manager

        self.__step_trackers: Dict[int, PositionTracker] = {}

        self.__single_controllers: Dict[int, ControllerProtocol] = {}
        self.__wave_controller: ControllerProtocol = WavePWMController(dispatcher, pigpio.get_pi(), thread_manager)

        self.__lock = threading.RLock()

        all_motors = motor_dao.get_all()
        for motor in all_motors:
            self.__step_trackers[motor.id] = PositionTracker(controller_id=motor.id,
                                                             dispatcher=dispatcher,
                                                             thread_manager=thread_manager)

    def start(self, controller_id: int, steps: int, freq_hz: int, forward: bool = True):
        if self.is_running(controller_id):
            raise ValueError(f"Motor is already running, cannot start.")

        controller = self.__get_single_controller(controller_id)
        controller.run(freq_hz=freq_hz, direction=forward, steps=steps)

    def start_wave(self, run_cmd: list[ControllerRunDto], pulse_us: int = 5):
        for cmd in run_cmd:
            if self.is_running(cmd.controller_id):
                raise ValueError(f"Motors are already running, cannot start.")

        self.__wave_controller.run(run_cmd=run_cmd, pulse_us=pulse_us)

    def stop(self, controller_id: int):
        controller = self.__get_single_controller(controller_id)
        controller.stop()

        if self.__wave_controller.status == EMotorStatus.RUNNING and self.__wave_controller.is_motor_in_use(controller_id):
            self.__wave_controller.stop()

    def stop_all(self) -> None:
        models = self.__motor_dao.get_all()
        for model in models:
            self.stop(model.id)

    def is_any_running(self) -> bool:
        models = self.__motor_dao.get_all()
        for model in models:
            if self.is_running(model.id):
                return True
        return False

    def is_running(self, motor_id: int) -> bool:
        controller = self.__get_single_controller(motor_id)
        return (controller.status == EMotorStatus.RUNNING) or (self.__wave_controller.is_motor_in_use(motor_id) and self.__wave_controller.status == EMotorStatus.RUNNING)

    def get_status(self, motor_id: int) -> EMotorStatus:
        if self.__wave_controller.status == EMotorStatus.RUNNING and self.__wave_controller.is_motor_in_use(motor_id):
            return EMotorStatus.RUNNING
        controller = self.__get_single_controller(motor_id)
        return controller.status

    def set_home(self, motor_id: int):
        tracker = self.__step_trackers.get(motor_id, None)
        if not tracker:
            print(f"No tracker found for motor: {motor_id}")
            return
        tracker.set_home()

    def get_position(self, motor_id: int) -> int:
        tracker = self.__step_trackers.get(motor_id, None)
        if not tracker:
            print(f"No tracker found for motor: {motor_id}")
            return 0
        return tracker.position

    def __get_single_controller(self, motor_id: int) -> SinglePWMController:
        with self.__lock:
            controller = self.__single_controllers.get(motor_id)
            if not controller:
                motor_model = self.__motor_dao.get_by_id(motor_id)
                config = self.__motor_dao.get_pin_config(motor_id)

                print(f"Creating controller for motor: {motor_id}")
                controller = SinglePWMController(
                    dispatcher=self._dispatcher,
                    pi=self.__pigpio_service.get_pi(),
                    thread_manager=self.__thread_manager,
                    controller_id=motor_id,
                    pin_enable= config.enable.pigpio_pin_number,
                    pin_forward= config.dir.pigpio_pin_number,
                    pin_step= config.steps.pigpio_pin_number
                )
                self.__single_controllers[motor_id] = controller
                print(f"Controller for motor: {motor_id} created.")
            if not controller.pi or not controller.pi.connected:
                print(f"Reconnecting pigpio in controller {motor_id}")
                controller.pi = self.__pigpio_service.get_pi()
            return controller

    def _subscribe_to_events(self):
        self._dispatcher.subscribe(ControllerStatusEvent, self.__handle_controller_status_change)

    def __handle_controller_status_change(self, event: ControllerStatusEvent):
        tracker = self.__step_trackers.get(event.motor_id, None)
        if not tracker:
            print(f"No tracker found for motor: {event.motor_id}")
            return
        if event.status == EMotorStatus.RUNNING:
            model = self.__motor_dao.get_by_id(event.motor_id)
            tracker.begin_motion(
                current_position=model.position,
                forward=event.direction,
                freq_hz=event.freq_hz
            )
        elif event.status == EMotorStatus.STOPPED:
            tracker.finish_motion()