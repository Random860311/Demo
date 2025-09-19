from typing import Protocol, Optional, Any, TypedDict, Unpack, runtime_checkable
import uuid

from event.pin_status_change_event import PinStatusChangeEvent
from servomotor.event.controller_event import MotorStatusData


class ExecKwargs(TypedDict, total=False):
    pass_limits: bool
    steps: int
    direction: bool
    current_position: int
    freq_hz: int

@runtime_checkable
class MotorTaskProtocol(Protocol):
    @property
    def uuid(self) -> uuid.UUID: ...

    @property
    def is_finished(self) -> Optional[bool]: ...

    def handle_controller_status_change(self, event: MotorStatusData) -> None:...

    def handle_pin_status_change(self, event: PinStatusChangeEvent) -> None: ...

    def execute(self, **kwargs: Unpack[ExecKwargs]) -> None: ...

    def stop(self) -> None: ...

@runtime_checkable
class SingleMotorTaskProtocol(MotorTaskProtocol, Protocol):
    @property
    def controller_id(self) -> int:...

    @property
    def current_direction(self) -> Optional[bool]:
        """
        Indicates the current movement direction.
        :return: None-> no movement, True -> clockwise, False -> counter-clockwise
        """
        ...



