from typing import Any

from flask_socketio import SocketIO

from common import utils
from core.event.event_dispatcher import EventDispatcher
from dto.motor_dto import MotorDto
from services.motor.motor_protocol import MotorServiceProtocol

from servomotor.controller_run_mode import EControllerRunMode
from web.events.motor_event import EMotorEventType, MotorUpdatedEvent, MotorCalibrationChangedEvent
from web.handlers.base_handler import BaseHandler


class MotorHandler(BaseHandler):
    def __init__(self, dispatcher: EventDispatcher, socketio: SocketIO, motor_services: MotorServiceProtocol):
        super().__init__(dispatcher, socketio)

        self.__motor_service = motor_services

    def register_handlers(self):
        self._socketio.on_event(message=EMotorEventType.GET_ALL, handler=self._handle_get_all)
        self._socketio.on_event(message=EMotorEventType.UPDATE, handler=self._handle_update_motor)
        self._socketio.on_event(message=EMotorEventType.STOP, handler=self._handle_stop_motor)
        self._socketio.on_event(message=EMotorEventType.START, handler=self._handle_start_motor)

        self._socketio.on_event(message=EMotorEventType.SET_ORIGIN_ALL, handler=self._handle_set_origin_all)
        self._socketio.on_event(message=EMotorEventType.SET_ORIGIN, handler=self._handle_set_origin)
        self._socketio.on_event(message=EMotorEventType.SET_LIMIT_ALL, handler=self._handle_set_limit_all)
        self._socketio.on_event(message=EMotorEventType.SET_LIMIT, handler=self._handle_set_limit)

        self._socketio.on_event(message=EMotorEventType.MOVE_TO_HOME, handler=self._handle_move_to_home)
        self._socketio.on_event(message=EMotorEventType.MOVE_TO_ORIGIN, handler=self._handle_move_to_origin)

        self._socketio.on_event(message=EMotorEventType.SET_CALIBRATION, handler=self._handle_set_calibration)
        self._socketio.on_event(message=EMotorEventType.GET_CALIBRATION, handler=self._handle_get_calibration)

        self._dispatcher.subscribe(MotorUpdatedEvent, self._emit_event)
        self._dispatcher.subscribe(MotorCalibrationChangedEvent, self._emit_event)

    @BaseHandler.safe(error_message="Error fetching motors calibration.")
    def _handle_get_calibration(self, data):
        return self.ok(obj={"calibrate": self.__motor_service.is_calibration_enabled()})

    @BaseHandler.safe(error_message="Error setting motors calibration.")
    def _handle_set_calibration(self, data):
        calibrate = utils.get_bool(data, "calibrate")
        self.__motor_service.set_calibration(calibrate)
        return self.ok()

    @BaseHandler.safe(error_message="Error moving motors to origin.")
    def _handle_move_to_origin(self, data):
        motor_id = utils.get_int(data, "motorId")
        self.__motor_service.move_to_origin(motor_id)
        return self.ok()

    @BaseHandler.safe(error_message="Error moving motors to home.")
    def _handle_move_to_home(self, data):
        motor_id = utils.get_int(data, "motorId")
        self.__motor_service.move_to_home(motor_id)
        return self.ok()

    @BaseHandler.safe(error_message="Error setting motors origin")
    def _handle_set_origin_all(self, data):
        self.__motor_service.set_origin_all()
        return self.ok()

    @BaseHandler.safe(error_message="Error setting motor origin.")
    def _handle_set_origin(self, data):
        motor_id = utils.get_int(data, "motorId")
        self.__motor_service.set_origin(motor_id)
        return self.ok()

    @BaseHandler.safe(error_message="Error setting all motors limits.")
    def _handle_set_limit_all(self, data):
        self.__motor_service.set_limit_all()
        return self.ok()

    @BaseHandler.safe(error_message="Error setting motor limit.")
    def _handle_set_limit(self, data):
        motor_id = utils.get_int(data, "motorId")
        self.__motor_service.set_limit(motor_id)
        return self.ok()

    @BaseHandler.safe(error_message="Error updating motor.")
    def _handle_get_all(self, data) -> dict[str, Any]:
        dto_list = self.__motor_service.get_all()
        motors = [dto.to_dict() for dto in dto_list]

        return self.ok(list_obj=motors)

    @BaseHandler.safe(error_message="Error updating motor.")
    def _handle_update_motor(self, data) -> dict[str, Any]:
        motor_dto = MotorDto.from_dict(data)
        motor_updated = self.__motor_service.update_motor(motor_dto)

        return self.ok(message=f"Motor {motor_updated.name} updated", obj_id=motor_updated.id)

    @BaseHandler.safe(error_message="Error stopping motor.")
    def _handle_stop_motor(self, data) -> dict[str, Any]:
        motor_id = utils.get_int(data, "motorId")
        self.__motor_service.stop_motor(motor_id)

        return self.ok(obj_id=motor_id)

    @BaseHandler.safe(error_message="Error starting motor.")
    def _handle_start_motor(self, data) -> dict[str, Any]:
        motor_id = utils.get_int(data, "motorId")
        direction = utils.get_bool(data, "direction", True)
        run_mode = EControllerRunMode.from_value(data.get("runMode", 0))

        motor = self.__motor_service.get_motor(motor_id)

        steps = 1
        match run_mode:
            case EControllerRunMode.INFINITE:
                steps = 0
            case EControllerRunMode.CONFIG:
                steps = utils.calculate_motor_total_steps(motor_angle=motor.angle, distance=data.get("distance"), distance_per_turn=motor.distance_per_turn)
            case _:
                steps = 1

        self.__motor_service.move_steps(motor_id=motor_id, steps=steps, forward=direction)

        return self.ok(obj_id=motor_id)

