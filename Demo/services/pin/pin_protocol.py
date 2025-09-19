from typing import Protocol, Optional

from db.model.pin.pin_model import PinModel
from dto.pin_dto import PinDto


def pin_model_to_dto(pin: PinModel) -> PinDto:
    return PinDto(
        id=pin.id,
        physical_pin_number=pin.physical_pin_number,
        pigpio_pin_number=pin.pigpio_pin_number,
        pin_type=pin.pin_type,
        description=pin.description,
    )

class PinProtocol(Protocol):
    def get_all(self) -> list[PinDto]:...

    def get_pin(self, pin_id: int) -> Optional[PinDto]:...

    def get_pin_id(self, gpio: int) -> int:...
