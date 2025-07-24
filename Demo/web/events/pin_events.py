# Demo/web/events/pin_events.py
from flask_socketio import SocketIO
from services import pin_service

def register_pin_events(socketio: SocketIO):
    @socketio.on("pin:get_all")
    def handle_get_all_pins(data):
        dto_list = pin_service.get_all()
        return [dto.to_dict() for dto in dto_list] #[dto.__dict__ for dto in dto_list]

    @socketio.on("pin:get_available")
    def handle_get_available_pins(data):
        dto_list = pin_service.get_available_pins()
        return [dto.to_dict() for dto in dto_list] #[dto.__dict__ for dto in dto_list]
