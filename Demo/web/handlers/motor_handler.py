import traceback
from typing import Any

from flask_socketio import SocketIO

from common import utils
from core.event.event_dispatcher import EventDispatcher
from dto.motor_dto import MotorDto


from services.motor_service import MotorService
from servomotor.controller_run_mode import EControllerRunMode
from web.events.motor_event import EMotorEventType, MotorUpdatedEvent
from web.events.response import Response, EStatusCode
from web.handlers.base_handler import BaseHandler


class MotorHandler(BaseHandler):
    def __init__(self, dispatcher: EventDispatcher, socketio: SocketIO, motor_services: MotorService):
        super().__init__(dispatcher, socketio)

        self.__motor_service = motor_services

    def register_handlers(self):
        self._socketio.on_event(message=EMotorEventType.GET_ALL, handler=self.handle_get_all)
        self._socketio.on_event(message=EMotorEventType.UPDATE, handler=self.handle_update_motor)
        self._socketio.on_event(message=EMotorEventType.STOP, handler=self.handle_stop_motor)
        self._socketio.on_event(message=EMotorEventType.START, handler=self.handle_start_motor)

        self._socketio.on_event(message=EMotorEventType.SET_HOME_ALL, handler=self.handle_set_home_all)
        self._socketio.on_event(message=EMotorEventType.SET_HOME, handler=self.handle_set_home)
        self._socketio.on_event(message=EMotorEventType.SET_ORIGIN_ALL, handler=self.handle_set_origin_all)
        self._socketio.on_event(message=EMotorEventType.SET_ORIGIN, handler=self.handle_set_origin)
        self._socketio.on_event(message=EMotorEventType.SET_LIMIT_ALL, handler=self.handle_set_limit_all)
        self._socketio.on_event(message=EMotorEventType.SET_LIMIT, handler=self.handle_set_limit)

        self._socketio.on_event(message=EMotorEventType.MOVE_TO_HOME_ALL, handler=self.handle_move_to_home_all)
        self._socketio.on_event(message=EMotorEventType.MOVE_TO_HOME, handler=self.handle_move_to_home)
        self._socketio.on_event(message=EMotorEventType.MOVE_TO_ORIGIN_ALL, handler=self.handle_move_to_origin_all)
        self._socketio.on_event(message=EMotorEventType.MOVE_TO_ORIGIN, handler=self.handle_move_to_origin)

        self._dispatcher.subscribe(MotorUpdatedEvent, self._emit_event)

    @BaseHandler.safe(error_message="Error setting motor calibration.")
    def handle_set_calibration(self, data):
        calibrate = utils.get_bool(data, "calibrate")
        self.__motor_service.calibrating = calibrate
        return self.ok()

    @BaseHandler.safe(error_message="Error moving motors to origin.")
    def handle_move_to_origin(self, data):
        motor_id = utils.get_int(data, "motorId")
        self.__motor_service.move_to_origin(motor_id)
        return self.ok()

    @BaseHandler.safe(error_message="Error moving motors to origin.")
    def handle_move_to_origin_all(self, data):
        self.__motor_service.move_to_origin_all()
        return self.ok()

    @BaseHandler.safe(error_message="Error moving motors to home.")
    def handle_move_to_home(self, data):
        motor_id = utils.get_int(data, "motorId")
        self.__motor_service.move_to_home(motor_id)
        return self.ok()

    @BaseHandler.safe(error_message="Error moving motors to home.")
    def handle_move_to_home_all(self, data):
        self.__motor_service.move_to_home_all()
        return self.ok()

    @BaseHandler.safe(error_message="Error setting motors origin")
    def handle_set_origin_all(self, data):
        self.__motor_service.set_origin_all()
        return self.ok()

    @BaseHandler.safe(error_message="Error setting motor origin.")
    def handle_set_origin(self, data):
        motor_id = utils.get_int(data, "motorId")
        self.__motor_service.set_origin(motor_id)
        return self.ok()

    @BaseHandler.safe(error_message="Error setting all motors home.")
    def handle_set_home_all(self, data):
        self.__motor_service.set_home_all()
        return self.ok()

    @BaseHandler.safe(error_message="Error setting motor home.")
    def handle_set_home(self, data):
        motor_id = utils.get_int(data, "motorId")
        self.__motor_service.set_home(motor_id)
        return self.ok()

    @BaseHandler.safe(error_message="Error setting all motors limits.")
    def handle_set_limit_all(self, data):
        self.__motor_service.set_limit_all()
        return self.ok()

    @BaseHandler.safe(error_message="Error setting motor limit.")
    def handle_set_limit(self, data):
        motor_id = utils.get_int(data, "motorId")
        self.__motor_service.set_limit(motor_id)
        return self.ok()


    @BaseHandler.safe(error_message="Error updating motor.")
    def handle_get_all(self, data) -> dict[str, Any]:
        dto_list = self.__motor_service.get_all()
        motors = [dto.to_dict() for dto in dto_list]

        return self.ok(list_obj=motors)

    @BaseHandler.safe(error_message="Error updating motor.")
    def handle_update_motor(self, data) -> dict[str, Any]:
        motor_dto = MotorDto.from_dict(data)
        motor_updated = self.__motor_service.update_motor(motor_dto)

        return self.ok(message=f"Motor {motor_updated.name} updated", obj_id=motor_updated.id)

    @BaseHandler.safe(error_message="Error stopping motor.")
    def handle_stop_motor(self, data) -> dict[str, Any]:
        motor_id = utils.get_int(data, "motorId")
        self.__motor_service.stop_motor(motor_id)

        return self.ok(obj_id=motor_id)

    @BaseHandler.safe(error_message="Error starting motor.")
    def handle_start_motor(self, data) -> dict[str, Any]:
        motor_id = utils.get_int(data, "motorId")
        direction = utils.get_bool(data, "direction", True)
        run_mode = EControllerRunMode.from_value(data.get("runMode", 0))
        self.__motor_service.run_motor(motor_id=motor_id, run_mode=run_mode, distance=data.get("distance"), forward=direction)

        return self.ok(obj_id=motor_id)

