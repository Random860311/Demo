import pigpio

pi = pigpio.pi()  # shared pigpio connection

used_pins: set[int] = set()

def is_pin_available(pin: int) -> bool:
    return pin not in used_pins

def are_pins_available(pins: list[int]) -> bool:
    return all(p not in used_pins for p in pins)

def register_pins(pins: list[int]) -> bool:
    if not are_pins_available(pins):
        return False
    used_pins.update(pins)
    return True

def release_pins(pins: list[int]):
    for p in pins:
        used_pins.discard(p)

def clear_all_pins():
    used_pins.clear()

def get_used_pins() -> list[int]:
    return sorted(used_pins)

