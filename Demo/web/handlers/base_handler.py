import functools
import traceback
from abc import ABC, abstractmethod
from dataclasses import is_dataclass, asdict
from enum import Enum
from typing import Any, Callable, TypeVar, ParamSpec, Optional

from flask_socketio import SocketIO

from core.error.base_error import BaseError
from core.event.base_event import BaseEvent
from core.event.event_dispatcher import EventDispatcher
from core.serializable import Serializable
from error.app_warning import AppWarning
from web.events.pin_event import EPinEventType
from web.events.response import Response, EStatusCode

P = ParamSpec("P")
R = TypeVar("R")

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

    @staticmethod
    def ok(**payload) -> dict[str, Any]:
        return Response(status_code=EStatusCode.SUCCESS, **payload).__dict__

    @staticmethod
    def fail(message: str, status_code:EStatusCode = EStatusCode.ERROR) -> dict[str, Any]:
        return Response(status_code=status_code, message=message).__dict__

    def log_error(self, where: str, err: Exception, *, bad_request: bool = False):
        prefix = "[BadRequest]" if bad_request else "[Error]"
        print(f"{prefix} {self.__class__.__name__}:{where}: {err}")
        traceback.print_exc()

    @staticmethod
    def safe(fn: Optional[Callable] = None, *, error_message: Optional[str] = None):
        """
        Decorator for handler methods.
        """
        def _decorator(func: Callable):
            @functools.wraps(func)
            def _wrapped(self: "BaseHandler", *args, **kwargs):
                # Use function name as the action label
                action_label = getattr(func, "__qualname__", func.__name__)
                try:
                    return func(self, *args, **kwargs)
                except AppWarning as aw:
                    self.log_error(action_label, aw)
                    return self.fail(aw.user_message, status_code=aw.code)
                except BaseError as be:
                    self.log_error(action_label, be)
                    return self.fail(be.user_message)
                except ValueError as ve:
                    self.log_error(action_label, ve, bad_request=True)
                    return self.fail(str(ve))
                except Exception as e:
                    self.log_error(action_label, e)
                    return self.fail(error_message if error_message else f"Error while trying to {func.__name__}.")
            return _wrapped

        # Support @BaseHandler.safe and @BaseHandler.safe()
        return _decorator if fn is None else _decorator(fn)

    @abstractmethod
    def register_handlers(self):
        pass
