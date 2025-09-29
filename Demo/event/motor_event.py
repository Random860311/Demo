from dataclasses import dataclass, field
import uuid
from typing import Optional

from db.model.motor.motor_model import MotorModel


@dataclass
class TaskEvent:
    task_id: uuid.UUID
    error: Optional[Exception] = field(default=None, kw_only=True)

@dataclass
class SingleMotorTaskEvent(TaskEvent):
    motor_id: int

@dataclass
class TaskHomeFinishedEvent(SingleMotorTaskEvent):
    pass

@dataclass
class TaskStepFinishedEvent(SingleMotorTaskEvent):
    pass

@dataclass
class TaskOriginFinishedEvent(SingleMotorTaskEvent):
    pass

@dataclass
class TaskGcodeFinishedEvent(TaskEvent):
    motor: Optional[MotorModel] = None

