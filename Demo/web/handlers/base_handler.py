from abc import ABC, abstractmethod
from dataclasses import is_dataclass, asdict
from enum import Enum

from flask_socketio import SocketIO

from core.event.base_event import BaseEvent
from core.event.event_dispatcher import EventDispatcher
from core.serializable import Serializable
from web.events.pin_event import EPinEventType


class BaseHandler(ABC):
    def __init__(self, dispatcher: EventDispatcher, socketio: SocketIO):
        self._dispatcher = dispatcher
        self._socketio = socketio

    def _emit_event(self, event: BaseEvent):
        try:
            data = BaseHandler._to_payload(event.data)
            # print("Emitting event: ", str(event.key), data)
            self._socketio.emit(event.key, data)
        except Exception as e:
            print("Error in _emit_event: ", str(e), str(event.key), event.__dict__)

    @staticmethod
    def _to_payload(obj):
        """Recursively convert objects (or collections of them) to JSON-serializable payloads."""
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj

        if isinstance(obj, Enum):
            return obj.value  # or obj.name

        if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
            return obj.to_dict()

        if is_dataclass(obj):
            return asdict(obj)

        if isinstance(obj, dict):
            return {k: BaseHandler._to_payload(v) for k, v in obj.items()}

        if isinstance(obj, (list, tuple, set)):
            return [BaseHandler._to_payload(v) for v in obj]

        if hasattr(obj, "__dict__"):
            # Avoid non-serializable internals by mapping its __dict__
            return {k: BaseHandler._to_payload(v) for k, v in vars(obj).items()}

        # Fallback: string representation
        return str(obj)

    @abstractmethod
    def register_handlers(self):
        pass