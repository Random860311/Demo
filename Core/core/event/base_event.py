from abc import ABC, abstractmethod
class Event(ABC):
    @abstractmethod
    def get_event_name(self) -> str:
        pass