import eventlet
eventlet.monkey_patch()

from services.pin.pin_protocol import PinProtocol
from services.motor.motor_protocol import MotorServiceProtocol
from services.pigpio.pigpio_protocol import PigpioProtocol
from services.controller.controller_protocol import ControllerProtocol
from services.config.config_protocol import ConfigProtocol
from services.config.config_service import ConfigService
from error.app_warning import AppWarning
from db.dao.config_dao import ConfigDao
from web.handlers.config_handler import ConfigHandler
from services.controller.controller_service import ControllerService
from event.app_event_dispatcher import AppEventDispatcher
from web.handlers.motor_handler import MotorHandler
from web.handlers.pin_handler import PinHandler
from db.dao.motor_dao import MotorDao
from db.dao.pin_dao import PinDao
from db.model.db_config import db_initialize, db_app
from services.pin.pin_service import PinService
from services.motor.motor_service import MotorService
from services.pigpio.pigpio_service import PigpioService
from core.event.event_dispatcher import EventDispatcher
from core.di_container import container
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from web.app import flask_app, socketio, handle_global_warning
import ssl
from pathlib import Path


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
    lambda: PinDao()
)

# Register MotorDao
motor_dao = MotorDao(flask_app, db_app, container.resolve_singleton(PinDao))
container.register_instance(MotorDao, motor_dao)

# Register ConfigDao
container.register_factory(
    ConfigDao,
    lambda: ConfigDao(flask_app, db_app)
)

# Register Services
# Register PigpioService
container.register_factory(PigpioProtocol, lambda: PigpioService(dispatcher=dispatcher,
                                                                 socketio=socketio))

# Register ControllerService
container.register_factory(
    ControllerProtocol,
    lambda: ControllerService(dispatcher=dispatcher,
                              socketio=socketio,
                              pigpio=container.resolve_singleton(PigpioProtocol),
                              motor_dao=motor_dao)
)

# Register PinService
container.register_factory(
    PinProtocol,
    lambda: PinService(dispatcher=dispatcher,
                       pigpio=container.resolve_singleton(PigpioProtocol),
                       socketio=socketio)
)

# Register MotorService
container.register_factory(
    MotorServiceProtocol,
    lambda: MotorService(dispatcher=dispatcher,
                         socketio=socketio,
                         pigpio=container.resolve_singleton(PigpioProtocol),
                         controller_service=container.resolve_singleton(ControllerProtocol),
                         motor_dao=container.resolve_singleton(MotorDao))
)

# Register ConfigService
container.register_factory(
    ConfigProtocol,
    lambda: ConfigService(dispatcher=dispatcher,
                          socketio=socketio,
                          config_dao=container.resolve_singleton(ConfigDao))
)

# Register SocketIO Handlers
# Register PinHandler
container.register_factory(
    PinHandler,
    lambda: PinHandler(dispatcher=dispatcher,
                       socketio=socketio,
                       pin_services=container.resolve_singleton(PinProtocol))
)

# Register MotorHandler
container.register_factory(
    MotorHandler,
    lambda: MotorHandler(dispatcher=dispatcher,
                         socketio=socketio,
                         motor_services=container.resolve_singleton(MotorServiceProtocol))
)

# Register ConfigHandler
container.register_factory(
    ConfigHandler,
    lambda: ConfigHandler(dispatcher=dispatcher,
                          socketio=socketio,
                          config_services=container.resolve_singleton(ConfigProtocol))
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
    cert_path = Path("web/certs/cert.pem")
    key_path = Path("web/certs/key.pem")

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_path, key_path)

    # Subscribe global handlers, init DB, resolve and register handlers
    dispatcher.subscribe(AppWarning, handle_global_warning)
    db_initialize()

    pin_handler = container.resolve_singleton(PinHandler)
    motor_handler = container.resolve_singleton(MotorHandler)
    config_handler = container.resolve_singleton(ConfigHandler)

    pin_service = container.resolve_singleton(PinProtocol)

    pin_handler.register_handlers()
    motor_handler.register_handlers()
    config_handler.register_handlers()

    # ---- SSL setup (HTTPS/WSS) ----
    has_tls = cert_path.exists() and key_path.exists()
    if has_tls:
        print(f"[TLS] Using cert: {cert_path} and key: {key_path}")
    else:
        if not cert_path.exists():
            print(f"[TLS] Missing certificate file: {cert_path}")
        if not key_path.exists():
            print(f"[TLS] Missing private key file: {key_path}")
        print("[TLS] TLS disabled (falling back to HTTP).")

    # Detect the async mode chosen by Flask-SocketIO (eventlet, gevent, threading, etc.)
    async_mode = getattr(socketio, "async_mode", None)
    print(f"[SocketIO] async_mode={async_mode}")

    run_kwargs = dict(
        host="0.0.0.0",
        port=8443,
        debug=True,
        # use_reloader=False,  # optional: disable duplicate startup logs
    )

    try:
        if has_tls:
            if async_mode in ("eventlet", "gevent"):
                # Eventlet/Gevent expect certfile/keyfile (NOT ssl_context)
                socketio.run(
                    flask_app,
                    certfile=str(cert_path),
                    keyfile=str(key_path),
                    **run_kwargs,
                )
            else:
                # Werkzeug/threading: ssl_context is supported
                ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                ssl_ctx.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
                socketio.run(
                    flask_app,
                    ssl_context=ssl_ctx,
                    **run_kwargs,
                )
        else:
            # No TLS → plain HTTP
            socketio.run(flask_app, **run_kwargs)

    except Exception as e:
        print(f"[TLS] Failed to start with TLS: {e}. Falling back to HTTP.")
        socketio.run(flask_app, **run_kwargs)


    # socketio.run(
    #     flask_app,
    #     host="0.0.0.0",
    #     port=8443,
    #     debug=True
    # )
