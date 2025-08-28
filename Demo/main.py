import eventlet
eventlet.monkey_patch()

from event.app_event_dispatcher import AppEventDispatcher

from core.dao.base_motor_dao import BaseMotorDao
from servomotor.tracker.position_tracker import PositionTracker

from web.handlers.motor_handler import MotorHandler
from web.handlers.pin_handler import PinHandler

from db.dao.motor_dao import MotorDao
from db.dao.pin_dao import PinDao
from db.model.db_config import db_initialize, db_app

from services.pin_service import PinService
from services.motor_service import MotorService
from services.pigpio_service import PigpioService

from core.event.event_dispatcher import EventDispatcher
from core.di_container import container

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

from web.app import flask_app, socketio
import ssl

# Register SQLAlchemy App
container.register_instance(SQLAlchemy, db_app)

# Register Flask App
container.register_instance(Flask, flask_app)

# Register SocketIO
container.register_instance(SocketIO, socketio)

# Register Event Manager
dispatcher = AppEventDispatcher(socketio)
container.register_instance(EventDispatcher, dispatcher)

# Register DAOs
# Register PinDao
container.register_factory(
    PinDao,
    lambda: PinDao(db_app)
)

# Register MotorDao
motor_dao = MotorDao(flask_app, db_app, container.resolve_singleton(PinDao))
container.register_instance(MotorDao, motor_dao)
container.register_instance(BaseMotorDao, motor_dao)

# Register Services
# Register PigpioService
container.register_factory(
    PigpioService,
    lambda: PigpioService(dispatcher=dispatcher,
                          motor_dao=motor_dao)
)

# Register PinService
container.register_factory(
    PinService,
    lambda: PinService(dispatcher=dispatcher,
                       pigpio=container.resolve_singleton(PigpioService),
                       socketio=socketio)
)

# Register MotorService
container.register_factory(
    MotorService,
    lambda: MotorService(dispatcher=dispatcher,
                         pigpio=container.resolve_singleton(PigpioService),
                         motor_dao=container.resolve_singleton(MotorDao))
)

# Register SocketIO Handlers
# Register PinHandler
container.register_factory(
    PinHandler,
    lambda: PinHandler(dispatcher=dispatcher,
                       socketio=socketio,
                       pin_services=container.resolve_singleton(PinService))
)

# Register MotorHandler
container.register_factory(
    MotorHandler,
    lambda: MotorHandler(dispatcher=dispatcher,
                         socketio=socketio,
                         motor_services=container.resolve_singleton(MotorService))
)

# Register Helpers
# container.register_factory(
#     PositionTracker,
#     lambda *args, **kwargs: PositionTracker()
# )
# container.register_factory(
#     PositionTracker,
#     lambda *args, **kwargs: PositionTracker(*args,
#                                             **{**kwargs, "events_dispatcher": dispatcher})

if __name__ == '__main__':
    cert_path = "web/certs/cert.pem"
    key_path = "web/certs/key.pem"

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_path, key_path)

    db_initialize()

    pin_handler = container.resolve_singleton(PinHandler)
    motor_handler = container.resolve_singleton(MotorHandler)
    pin_service = container.resolve_singleton(PinService)

    pin_handler.register_handlers()
    motor_handler.register_handlers()

    pin_service.start_listening_pins()

    socketio.run(
        flask_app,
        host="0.0.0.0",
        port=8443,
        # certfile=cert_path,
        # keyfile=key_path,
        # ssl_context=(cert_path, key_path),
        debug=True
    )

    # app.app.run(
    #     host="0.0.0.0",
    #     port=8443, #8000
    #     ssl_context=(cert_path, key_path),
    #     debug=True
    # )