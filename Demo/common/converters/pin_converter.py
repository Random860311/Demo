from dto.pin_dto import PinDto
from db.model.pin_model import PinModel

def pin_model_to_dto(pin: PinModel) -> PinDto:
    return PinDto(
        id=pin.id,
        physical_pin_number=pin.physical_pin_number,
        pigpio_pin_number=pin.pigpio_pin_number,
        pin_type=pin.pin_type,
        description=pin.description,
        in_use=pin.in_use
    )