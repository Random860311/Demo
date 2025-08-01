from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from db.model.db_config import db_app

import traceback

from web.events.responses import Response, EStatusCode

flask_app = Flask(__name__)

CORS(flask_app)

flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///demo.db"
flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db_app.init_app(flask_app)

# Create SocketIO server (using asyncio) , async_mode="asgi"
socketio = SocketIO(flask_app, cors_allowed_origins="*")



@socketio.on_error_default
def global_socketio_error_handler(e):
    print("Uncaught SocketIO exception: ", e)
    traceback.print_exc()
    return Response(status_code=EStatusCode.ERROR, message="Internal server error. Please try again later.").__dict__
    # return {
    #     "status": "error",
    #     "message": "Internal server error. Please try again later."
    # }





