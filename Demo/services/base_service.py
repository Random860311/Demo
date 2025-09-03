from core.event.event_dispatcher import EventDispatcher
from abc import ABC, abstractmethod


class BaseService(ABC):
    def __init__(self, dispatcher: EventDispatcher):
        self._dispatcher = dispatcher

    def _subscribe_to_events(self):
        pass