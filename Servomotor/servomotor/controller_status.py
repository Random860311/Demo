from enum import Enum

class EMotorStatus(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    FAULTED = "faulted"