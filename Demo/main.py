import eventlet
eventlet.monkey_patch()

from web.handlers.motor_handler import MotorHandler
from web.handlers.pin_handler import PinHandler

from db.dao.motor_dao import MotorDao
from db.dao.pin_dao import PinDao
from db.model.db_config import db_initialize, db_app

from services.pin_service import PinService
from services.motor_service import MotorService
from services.pigpio_service import PigpioService

from core.event.event_dispatcher import EventDispatcher, dispatcher
from core.di_container import container

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

from web.app import flask_app, socketio
import ssl


container.register_instance(SQLAlchemy, db_app)
container.register_instance(Flask, flask_app)
container.register_instance(SocketIO, socketio)
container.register_instance(EventDispatcher, dispatcher)

container.register_singleton(PinDao, lambda: PinDao(db_app))
container.register_singleton(MotorDao, lambda : MotorDao(db_app, container.resolve(PinDao)))

container.register_singleton(PigpioService, lambda: PigpioService())
container.register_singleton(PinService, lambda: PinService())
container.register_singleton(MotorService, lambda: MotorService(dispatcher=dispatcher,
                                                                pigpio=container.resolve(PigpioService),
                                                                motor_dao=container.resolve(MotorDao)))

container.register_singleton(PinHandler, lambda: PinHandler(dispatcher=dispatcher,
                                                            socketio=socketio,
                                                            pin_services=container.resolve(PinService)))
container.register_singleton(MotorHandler, lambda: MotorHandler(dispatcher=dispatcher,
                                                                socketio=socketio,
                                                                motor_services=container.resolve(MotorService)))

if __name__ == '__main__':
    cert_path = "web/certs/cert.pem"
    key_path = "web/certs/key.pem"

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_path, key_path)

    db_initialize()

    pin_handler = container.resolve(PinHandler)
    motor_handler = container.resolve(MotorHandler)

    pin_handler.register_handlers()
    motor_handler.register_handlers()

    print("SocketIO async_mode:", socketio.async_mode)
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