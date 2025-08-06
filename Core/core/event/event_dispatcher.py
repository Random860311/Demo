from threading import Lock
from typing import Callable, Dict, List, Any, TypeVar, Type, Union
from core.event.base_event import BaseEvent
import inspect
import asyncio

E = TypeVar("E", bound=BaseEvent)

class EventDispatcher:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[BaseEvent], None]]] = {}
        self._lock = Lock()

    @staticmethod
    def resolve_event_name(event: Union[Type[E] | str]) -> str:
        if isinstance(event, str):
            return event
        elif issubclass(event, BaseEvent):
            return event.__name__
        else:
            raise ValueError("event must be a string or BaseEvent subclass")

    def subscribe(self, event: Union[Type[E] | str], callback: Callable[[E], None]):
        event_name = EventDispatcher.resolve_event_name(event)
        with self._lock:
            self._subscribers.setdefault(event_name, []).append(callback)

    def unsubscribe(self, event: str, callback: Callable[[E], None]):
        event_name = EventDispatcher.resolve_event_name(event)
        with self._lock:
            if event_name in self._subscribers and callback in self._subscribers[event_name]:
                self._subscribers[event_name].remove(callback)

    def emit(self, event: E):
        with self._lock:
            event_name = EventDispatcher.resolve_event_name(type(event))
            callbacks = list(self._subscribers.get(event_name, []))
            if not callbacks:
                callbacks = list(self._subscribers.get(event.key, []))

        for cb in callbacks:
            try:
                if inspect.iscoroutinefunction(cb):
                    asyncio.create_task(cb(event))
                else:
                    cb(event)
            except Exception as e:
                print(f"Error in subscriber '{cb}': {e}")
                # logger.error(f"Error in subscriber '{cb}': {e}")


# Singleton instance
dispatcher = EventDispatcher()