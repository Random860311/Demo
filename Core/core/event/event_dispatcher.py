from threading import Lock
from typing import Callable, Dict, List, Any, TypeVar
from core.event.base_event import BaseEvent
import inspect
import asyncio

E = TypeVar("E", bound=BaseEvent)

class EventDispatcher:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[BaseEvent], None]]] = {}
        self._lock = Lock()

    def subscribe(self, event_name: str, callback: Callable[[E], None]):
        with self._lock:
            self._subscribers.setdefault(event_name, []).append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[[E], None]):
        with self._lock:
            if event_name in self._subscribers and callback in self._subscribers[event_name]:
                self._subscribers[event_name].remove(callback)

    def emit(self, event: E):
        with self._lock:
            callbacks = list(self._subscribers.get(event.event_name, []))

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