from abc import ABC, abstractmethod
from threading import Lock
from typing import Callable, Dict, List, Any, TypeVar, Type, Union
from core.event.base_event import BaseEvent
import inspect

E = TypeVar("E")

class EventDispatcher(ABC):
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[BaseEvent], None]]] = {}
        self._lock = Lock()

    @staticmethod
    def resolve_event_name(event: Union[Type[E] | str]) -> str:
        if isinstance(event, str):
            return event
        return event.__name__

    def subscribe(self, event: Union[Type[E] | str], callback: Callable[[E], None]):
        event_name = EventDispatcher.resolve_event_name(event)
        with self._lock:
            self._subscribers.setdefault(event_name, []).append(callback)

    def unsubscribe(self, event: str, callback: Callable[[E], None]):
        event_name = EventDispatcher.resolve_event_name(event)
        with self._lock:
            if event_name in self._subscribers and callback in self._subscribers[event_name]:
                self._subscribers[event_name].remove(callback)

    def _collect_callbacks(self, event: E):
        with self._lock:
            event_name = EventDispatcher.resolve_event_name(type(event))
            callbacks = list(self._subscribers.get(event_name, []))
            # if not callbacks:
            #     callbacks = list(self._subscribers.get(event.key, []))
        return callbacks

    def emit(self, event: E):
        callbacks = self._collect_callbacks(event)

        for cb in callbacks:
            EventDispatcher._run_cb_safely(cb, event)

    @abstractmethod
    def emit_async(self, event: E):
        pass

    @staticmethod
    def _run_cb_safely(cb: Callable[[Any], Any], event: Any):
        try:
            # In eventlet mode, prefer sync callbacks.
            if inspect.iscoroutinefunction(cb):
                # Strongly recommended to avoid async defs in eventlet mode,
                # but if present, run to completion in a temporary loop:
                import asyncio
                asyncio.run(cb(event))
            else:
                cb(event)
        except Exception as e:
            print(f"[dispatcher.emit_async] subscriber error in {cb}: {e}")


