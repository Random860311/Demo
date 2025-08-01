from enum import Enum

class MotorStatus(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    FAULTED = "faulted"

    def get_event_name(self) -> str:
        return self