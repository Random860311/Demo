from threading import Lock
from typing import Callable, Dict, List
from core.event.base_event import Event

class EventDispatcher:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = Lock()

    def subscribe(self, event: Event, callback: Callable):
        event_name = event.get_event_name()
        with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            if callback not in self._subscribers[event_name]:
                self._subscribers[event_name].append(callback)

    def unsubscribe(self, event: Event, callback: Callable):
        event_name = event.get_event_name()
        with self._lock:
            if event_name in self._subscribers and callback in self._subscribers[event_name]:
                self._subscribers[event_name].remove(callback)

    def emit(self, event: Event, *args, **kwargs):
        event_name = event.get_event_name()
        with self._lock:
            callbacks = list(self._subscribers.get(event_name, []))
        for cb in callbacks:
            cb(*args, **kwargs)


# Singleton instance
dispatcher = EventDispatcher()