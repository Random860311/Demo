from flask_socketio import SocketIO

from core.event.event_dispatcher import EventDispatcher, E
from services.pigpio_service import PigpioService


class AppEventDispatcher(EventDispatcher):
    def __init__(self, socketio: SocketIO):
        super().__init__()
        self.__socketio = socketio

    def emit_async(self, event: E):
        callbacks = self._collect_callbacks(event)
        # if self.__socketio is None:
        #     # Fallback without socketio: spawn greenlets directly
        #     import eventlet
        #     for cb in callbacks:
        #         eventlet.spawn_n(self._run_cb_safely, cb, event)
        #     return

        # Use Socket.IO's background task helper (works for eventlet/gevent/threading modes)
        for cb in callbacks:
            self.__socketio.start_background_task(self._run_cb_safely, cb, event)


