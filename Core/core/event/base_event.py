from abc import ABC
from typing import TypeVar, Generic, Optional, Any

from core.serializable import Serializable

EventData = TypeVar("EventData")

class BaseEvent(Generic[EventData], ABC):
    def __init__(self, key: str, data: Optional[EventData] = None):
        self.key = key
        self.data = data