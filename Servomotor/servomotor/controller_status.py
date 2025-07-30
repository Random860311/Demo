from enum import Enum
from core.event.base_event import Event

class MotorStatus(str, Enum, Event):
    STOPPED = "stopped"
    RUNNING = "running"
    FAULTED = "faulted"

    def get_event_name(self) -> str:
        return self