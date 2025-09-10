from enum import Enum


class EGlobalEvent(str, Enum):
    WARNING = "app:warning"
    ERROR = "app:error"