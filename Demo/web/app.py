from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from db.model import db_config

from web.events.motor_events import register_motor_events
from web.events.pin_events import register_pin_events
import traceback

app = Flask(__name__)

CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///demo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db_config.db_obj.init_app(app)

# Create SocketIO server (using asyncio) , async_mode="asgi"
socketio = SocketIO(app, cors_allowed_origins="*")

# Register WebSocket event handlers
register_motor_events(socketio)
register_pin_events(socketio)

# @app.before_request
# def create_tables():
#     db_config.initialize()

@socketio.on_error_default
def global_socketio_error_handler(e):
    print("Uncaught SocketIO exception: ", e)
    traceback.print_exc()
    return {
        "status": "error",
        "message": "Internal server error. Please try again later."
    }





