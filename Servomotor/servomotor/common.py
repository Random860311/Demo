from enum import Enum

class MotorStatus(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    FAULTED = "faulted"