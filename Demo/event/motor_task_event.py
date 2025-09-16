from dataclasses import dataclass
import uuid

@dataclass
class TaskEvent:
    motor_id: int
    task_id: uuid.UUID

@dataclass
class TaskHomeFinishedEvent(TaskEvent):
    pass

@dataclass
class TaskStepFinishedEvent(TaskEvent):
    pass

@dataclass
class TaskOriginFinishedEvent(TaskEvent):
    pass