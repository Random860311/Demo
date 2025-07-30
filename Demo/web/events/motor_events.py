from flask_socketio import SocketIO
from dto.motor_dto import MotorDto
from services import motor_service
import time

def register_motor_events(socketio: SocketIO):
    @socketio.on("motor:get_all")
    def handle_get_all(data):
        #time.sleep(5)
        try:
            dto_list = motor_service.get_all()
            motors = [dto.to_dict() for dto in dto_list]
            return motors#[dto.__dict__ for dto in dto_list]
        except Exception as e:
            print("Error:", e)
            return {"status": "error"}

    @socketio.on("motor:update")
    def handle_update_motor(data):
        motor_dto = MotorDto.from_dict(data)
        motor_updated = motor_service.update_motor(motor_dto)

        # Notify all clients
        socketio.emit("motor:updated", motor_updated.to_dict())  # socketio.emit("motor:updated", motor.__dict__)
        return {"status": "success", "motor_id": motor_updated.id}
        # try:
        #
        # except Exception as e:
        #     print("Error:", e)
        #     return {"status": "error"}

    @socketio.on("motor:start")
    def handle_start_motor(data):
        motor_id = data.get("motorId")
        direction = data.get("direction", True)
        infinite = data.get("infinite", False)

        print("Start motor", motor_id, direction, infinite)

        if not isinstance(direction, bool):
            return {"status": "error", "message": "'direction' must be a boolean."}

        try:
            motor_service.run_motor(motor_id, forward=direction, infinite = infinite)
            return {
                "status": "success",
                "message": f"Motor {motor_id} started",
                "direction": direction,
            }
        except KeyError:
            return {"status": "error", "message": f"Motor {motor_id} not found."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @socketio.on("motor:stop")
    def handle_stop_motor(data):
        motor_id = data.get("motorId")
        print("Stop motor", motor_id)
        try:
            motor_service.stop_motor(motor_id)
            return {"status": "success", "message": f"Motor {motor_id} stopped"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
