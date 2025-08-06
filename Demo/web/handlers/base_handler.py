from abc import ABC

from core.event.event_dispatcher import EventDispatcher


class BaseHandler(ABC):
    def __init__(self, dispatcher: EventDispatcher):
        self._dispatcher = dispatcher