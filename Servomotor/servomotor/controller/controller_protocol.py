from typing import Protocol, runtime_checkable, TypedDict, Unpack
import pigpio

from servomotor.dto.controller_status import EMotorStatus
from servomotor.dto.run_cmd_dto import ControllerRunDto


class RunKwargs(TypedDict, total=False):
    steps: int
    direction: bool
    freq_hz: int
    pulse_us: int
    run_cmd: list[ControllerRunDto]
    duty: int

@runtime_checkable
class ControllerProtocol(Protocol):
    @property
    def pi(self) -> pigpio.pi:...

    @pi.setter
    def pi(self, value: pigpio.pi):...

    @property
    def status(self) -> EMotorStatus:...

    def stop(self) -> bool:...

    def run(self, **kwargs: Unpack[RunKwargs]):...

    def is_motor_in_use(self, motor_id: int) -> bool:...