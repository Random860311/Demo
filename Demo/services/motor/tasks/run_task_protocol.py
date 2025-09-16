from typing import Protocol, Optional, Any, TypedDict, Unpack
import uuid

from event.pin_status_change_event import PinStatusChangeEvent
from servomotor.event.controller_event import MotorStatusData


class ExecKwargs(TypedDict, total=False):
    pass_limits: bool
    steps: int
    direction: bool

class RunTaskProtocol(Protocol):
    @property
    def uuid(self) -> uuid.UUID:...

    @property
    def controller_id(self) -> int:...

    @property
    def is_finished(self) -> Optional[bool]:...

    def handle_controller_status_change(self, event: MotorStatusData) -> None:...

    def handle_pin_status_change(self, event: PinStatusChangeEvent) -> None: ...

    def execute(self, **kwargs: Unpack[ExecKwargs]) -> None: ...

    def stop(self) -> None: ...
