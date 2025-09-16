from flask_socketio import SocketIO

from core.event.event_dispatcher import EventDispatcher
from abc import ABC, abstractmethod


class BaseService(ABC):
    def __init__(self, dispatcher: EventDispatcher, socketio: SocketIO):
        self._dispatcher = dispatcher
        self._socketio = socketio

    def _subscribe_to_events(self):
        pass