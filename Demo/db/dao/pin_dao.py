from db.model.pin_model import PinModel, PIN_MAP
from common.PinType import PinType
from db.model.db_config import db_obj

def seed_default_pins():
    if PinModel.query.count() > 0:
        print("[Pin Seed] Pins already exist. Skipping.")
        return
    print("[Pins] Populating pin table...")
    pins = []
    for physical, bcm, desc, ptype in PIN_MAP:
        pin = PinModel(
            physical_pin_number=physical,
            pigpio_pin_number=bcm,
            description=desc,
            pin_type=ptype,
            in_use=False
        )
        pins.append(pin)
    db_obj.session.add_all(pins)
    db_obj.session.commit()
    print(f"[Pins] Inserted {len(pins)} pins.")

def find_pin_by_gpio_number(number: int) -> PinModel:
    pin = PinModel.query.filter_by(pigpio_pin_number=number).first()
    if not pin:
        raise ValueError(f"GPIO pin {number} not found in DB.")
    return pin

def find_pin_by_physical_number(number: int) -> PinModel:
    pin = PinModel.query.filter_by(physical_pin_number=number).first()
    if not pin:
        raise ValueError(f"Physical pin {number} not found in DB.")
    return pin