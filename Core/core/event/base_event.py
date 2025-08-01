from abc import ABC
from typing import TypeVar, Generic, Optional

EventData = TypeVar("EventData")

class BaseEvent(Generic[EventData], ABC):
    def __init__(self, event_name: str, data: Optional[EventData] = None):
        self.event_name = event_name
        self.data = data

