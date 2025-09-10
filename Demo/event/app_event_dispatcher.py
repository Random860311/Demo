from flask_socketio import SocketIO

from core.event.event_dispatcher import EventDispatcher, E
import traceback


class AppEventDispatcher(EventDispatcher):
    def __init__(self, socketio: SocketIO):
        super().__init__()
        self.__socketio = socketio

    def emit_async(self, event: E):
        callbacks = self._collect_callbacks(event)
        # print("Emitting event: ", "".join(traceback.format_stack()))
        for cb in callbacks:
            self.__socketio.start_background_task(self._run_cb_safely, cb, event)


