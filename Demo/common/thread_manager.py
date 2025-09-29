import traceback

from flask_socketio import SocketIO

from core.thread_manager import ThreadManagerProtocol


class ThreadManager(ThreadManagerProtocol):
    def __init__(self, socketio: SocketIO):
        self.__socketio = socketio

    def start_background_task(self, target, *args, **kwargs):
        try:
            return self.__socketio.start_background_task(target, *args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            print(f"Error starting background task: {e}")
            raise