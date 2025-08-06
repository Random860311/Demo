from typing import Any

from flask_socketio import SocketIO

from core.event.base_event import BaseEvent
from core.event.event_dispatcher import EventDispatcher
from core.serializable import Serializable
from dto.motor_dto import MotorDto


from services.motor_service import MotorService
from web.events.motor_event import MotorEventType, MotorUpdatedEvent, MotorStatusChangedEvent
from web.events.response import Response, EStatusCode
from web.handlers.base_handler import BaseHandler


class MotorHandler(BaseHandler):
    def __init__(self, dispatcher: EventDispatcher, socketio: SocketIO, motor_services: MotorService):
        super().__init__(dispatcher)
        self.__socketio = socketio
        self.__motor_service = motor_services

    def register_handlers(self):
        self.__socketio.on_event(message=MotorEventType.GET_ALL, handler=self.handle_get_all)
        self.__socketio.on_event(message=MotorEventType.UPDATE, handler=self.handle_update_motor)
        self.__socketio.on_event(message=MotorEventType.STOP, handler=self.handle_stop_motor)
        self.__socketio.on_event(message=MotorEventType.START, handler=self.handle_start_motor)

        self._dispatcher.subscribe(MotorUpdatedEvent, self._emit_event)
        self._dispatcher.subscribe(MotorStatusChangedEvent, self._emit_event)

    def _emit_event(self, event: BaseEvent):
        try:
            data = event.data.to_dict() if isinstance(event.data, Serializable) else event.data.__dict__ if event.data else None
            self.__socketio.emit(event.key, data)
        except Exception as e:
            print("Error in MotorHandler, _emit_event: ", str(e), str(event.key), event.__dict__)

    def handle_get_all(self, data) -> dict[str, Any]:
        try:
            dto_list = self.__motor_service.get_all()
            motors = [dto.to_dict() for dto in dto_list]

            return Response(status_code=EStatusCode.SUCCESS, list_obj=motors).__dict__
            # return motors
        except Exception as e:
            print("Error in MotorHandler, handle_get_all: ", str(e))
            return Response(status_code=EStatusCode.ERROR, message="Error fetching motors.").__dict__
            # return {"status": "error"}

    def handle_update_motor(self, data) -> dict[str, Any]:
        try:
            motor_dto = MotorDto.from_dict(data)
            motor_updated = self.__motor_service.update_motor(motor_dto)

            return Response(status_code=EStatusCode.SUCCESS, message=f"Motor {motor_dto.name} updated", obj_id=motor_dto.id).__dict__

            # self.__socketio.emit("motor:updated", motor_updated.to_dict())  # socketio.emit("motor:updated", motor.__dict__)
            # return {"status": "success", "motor_id": motor_updated.id}
        except Exception as e:
            print("Error in MotorHandler, handle_update_motor: ", str(e))
            return Response(status_code=EStatusCode.ERROR, message="Error updating motor.").__dict__

    def handle_stop_motor(self, data) -> dict[str, Any]:
        try:
            motor_id = data.get("motorId")
            print("Stop motor", motor_id)
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
            infinite = data.get("infinite", False)

            print("Start motor", motor_id, direction, infinite)
            self.__motor_service.run_motor(motor_id, forward=direction, infinite = infinite)
            return Response(status_code=EStatusCode.SUCCESS, message="Motor started", obj_id=motor_id).__dict__
            # return {
            #     "status": "success",
            #     "message": f"Motor {motor_id} started",
            #     "direction": direction,
            # }
        except Exception as e:
            print("Error in MotorHandler, handle_start_motor: ", str(e))
            return Response(status_code=EStatusCode.ERROR, message="Error starting motor.").__dict__
            # return {"status": "error", "message": str(e)}
#
# def register_motor_events(socketio: SocketIO):
#     @socketio.on("motor:get_all")
#     def handle_get_all(data):
#         #time.sleep(5)
#         try:
#             dto_list = motor_service.get_all()
#             motors = [dto.to_dict() for dto in dto_list]
#             return motors#[dto.__dict__ for dto in dto_list]
#         except Exception as e:
#             print("Error:", e)
#             return {"status": "error"}
#
#     @socketio.on("motor:update")
#     def handle_update_motor(data):
#         motor_dto = MotorDto.from_dict(data)
#         motor_updated = motor_service.update_motor(motor_dto)
#
#         socketio.emit("motor:updated", motor_updated.to_dict())  # socketio.emit("motor:updated", motor.__dict__)
#         return {"status": "success", "motor_id": motor_updated.id}
#
#
#     @socketio.on("motor:start")
#     def handle_start_motor(data):
#         motor_id = data.get("motorId")
#         direction = data.get("direction", True)
#         infinite = data.get("infinite", False)
#
#         print("Start motor", motor_id, direction, infinite)
#
#         if not isinstance(direction, bool):
#             return {"status": "error", "message": "'direction' must be a boolean."}
#
#         try:
#             motor_service.run_motor(motor_id, forward=direction, infinite = infinite)
#             return {
#                 "status": "success",
#                 "message": f"Motor {motor_id} started",
#                 "direction": direction,
#             }
#         except KeyError:
#             return {"status": "error", "message": f"Motor {motor_id} not found."}
#         except Exception as e:
#             return {"status": "error", "message": str(e)}
#
#     @socketio.on("motor:stop")
#     def handle_stop_motor(data):
#         motor_id = data.get("motorId")
#         print("Stop motor", motor_id)
#         try:
#             motor_service.stop_motor(motor_id)
#             return {"status": "success", "message": f"Motor {motor_id} stopped"}
#         except Exception as e:
#             return {"status": "error", "message": str(e)}
