from dataclasses import dataclass
from typing import Optional


@dataclass
class ControllerRunDto:
    controller_id: int
    steps: int
    freq_hz: int
    direction: bool # True => Clockwise, False => Counter-clockwise
    gpio_step: int
    gpio_home: int
    gpio_direction: int
    gpio_enable: Optional[int] = None
    gpio_alarm: Optional[int] = None