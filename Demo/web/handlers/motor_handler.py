from typing import Any

from flask_socketio import SocketIO

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
        self._socketio.on_event(message=EMotorEventType.SET_ORIGIN_ALL, handler=self.handle_set_origin_all)
        self._socketio.on_event(message=EMotorEventType.MOVE_TO_HOME_ALL, handler=self.handle_move_to_home_all)
        self._socketio.on_event(message=EMotorEventType.MOVE_TO_HOME, handler=self.handle_move_to_home)
        self._socketio.on_event(message=EMotorEventType.MOVE_TO_ORIGIN_ALL, handler=self.handle_move_to_origin_all)
        self._socketio.on_event(message=EMotorEventType.MOVE_TO_ORIGIN, handler=self.handle_move_to_origin)

        self._dispatcher.subscribe(MotorUpdatedEvent, self._emit_event)

    def handle_move_to_origin(self, data):
        try:
            self.__motor_service.move_to_origin(int(data.get("motorId")))

            return Response(status_code=EStatusCode.SUCCESS).__dict__
        except Exception as e:
            print(f"Error in MotorHandler, handle_move_to_origin: {data}", str(e))
            return Response(status_code=EStatusCode.ERROR, message="Error moving motors to origin.").__dict__


    def handle_move_to_origin_all(self, data):
        try:
            self.__motor_service.move_to_origin_all()

            return Response(status_code=EStatusCode.SUCCESS).__dict__
        except Exception as e:
            print("Error in MotorHandler, handle_move_to_origin_all: ", str(e))
            return Response(status_code=EStatusCode.ERROR, message="Error moving motors to origin.").__dict__

    def handle_move_to_home(self, data):
        try:
            self.__motor_service.move_to_home(int(data.get("motorId")))
            return Response(status_code=EStatusCode.SUCCESS).__dict__
        except Exception as e:
            print(f"Error in MotorHandler, handle_move_to_home: {data}", str(e))
            return Response(status_code=EStatusCode.ERROR, message="Error moving motors to home.").__dict__

    def handle_move_to_home_all(self, data):
        try:
            self.__motor_service.move_to_home_all()

            return Response(status_code=EStatusCode.SUCCESS).__dict__
        except Exception as e:
            print("Error in MotorHandler, handle_move_to_home_all: ", str(e))
            return Response(status_code=EStatusCode.ERROR, message="Error moving motors to home.").__dict__

    def handle_set_origin_all(self, data):
        try:
            self.__motor_service.set_origin_all()

            return Response(status_code=EStatusCode.SUCCESS).__dict__
        except Exception as e:
            print("Error in MotorHandler, handle_set_origin_all: ", str(e))
            return Response(status_code=EStatusCode.ERROR, message="Error setting motors origin.").__dict__

    def handle_set_home_all(self, data):
        try:
            self.__motor_service.set_home_all()

            return Response(status_code=EStatusCode.SUCCESS).__dict__
        except Exception as e:
            print("Error in MotorHandler, handle_set_home_all: ", str(e))
            return Response(status_code=EStatusCode.ERROR, message="Error setting motors home.").__dict__

    def handle_get_all(self, data) -> dict[str, Any]:
        try:
            dto_list = self.__motor_service.get_all()
            motors = [dto.to_dict() for dto in dto_list]

            return Response(status_code=EStatusCode.SUCCESS, list_obj=motors).__dict__
        except Exception as e:
            print("Error in MotorHandler, handle_get_all: ", str(e))
            return Response(status_code=EStatusCode.ERROR, message="Error fetching motors.").__dict__

    def handle_update_motor(self, data) -> dict[str, Any]:
        try:
            motor_dto = MotorDto.from_dict(data)
            motor_updated = self.__motor_service.update_motor(motor_dto)

            return Response(status_code=EStatusCode.SUCCESS, message=f"Motor {motor_updated.name} updated", obj_id=motor_updated.id).__dict__
        except Exception as e:
            print("Error in MotorHandler, handle_update_motor: ", str(e))
            return Response(status_code=EStatusCode.ERROR, message="Error updating motor.").__dict__

    def handle_stop_motor(self, data) -> dict[str, Any]:
        try:
            motor_id = data.get("motorId")
            self.__motor_service.stop_motor(motor_id)

            return Response(status_code=EStatusCode.SUCCESS, message="Motor updated", obj_id=motor_id).__dict__
            # return {"status": "success", "message": f"Motor {motor_id} stopped"}
        except Exception as e:
            print("Error in MotorEvents, handle_stop_motor: ", str(e))
            return Response(status_code=EStatusCode.ERROR, message="Error stopping motor.").__dict__
            # return {"status": "error", "message": str(e)}

    def handle_start_motor(self, data) -> dict[str, Any]:
        try:
            motor_id = data.get("motorId")
            direction = data.get("direction", True)
            run_mode = EControllerRunMode.from_value(data.get("runMode", 0))

            self.__motor_service.run_motor(motor_id, forward=direction, run_mode= run_mode)
            return Response(status_code=EStatusCode.SUCCESS, message="Motor started", obj_id=motor_id).__dict__
        except Exception as e:
            print("Error in MotorHandler, handle_start_motor: ", str(e))
            return Response(status_code=EStatusCode.ERROR, message="Error starting motor.").__dict__

