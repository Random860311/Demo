from dataclasses import dataclass


@dataclass
class PinStatusChangeEvent:
    pin_id: int
    pigpio_pin_number: int
    status: bool
