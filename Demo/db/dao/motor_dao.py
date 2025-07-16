from db.model.motor_model import MotorModel
from db.dao import pin_dao
from db.model.db_config import db_obj


def seed_default_motors():
    if MotorModel.query.count() > 0:
        print("[Motor Seed] Motors already exist. Skipping.")
        return

    pin_dao.seed_default_pins()

    print("[Motor Seed] Creating default motors...")
    motor_configs = [
        {
            "id": 1,
            "name": "Motor 1",
            "step": 12,
            "dir": 16,
            "enable": 20
        },
        {
            "id": 2,
            "name": "Motor 2",
            "step": 13,
            "dir": 17,
            "enable": 21
        },
        {
            "id": 3,
            "name": "Motor 3",
            "step": 18,
            "dir": 22,
            "enable": 23
        },
        {
            "id": 4,
            "name": "Motor 4",
            "step": 19,
            "dir": 24,
            "enable": 25
        },
    ]
    for cfg in motor_configs:
        pin_step = pin_dao.find_pin_by_gpio_number(cfg["step"])
        pin_forward = pin_dao.find_pin_by_gpio_number(cfg["dir"])
        pin_enable = pin_dao.find_pin_by_gpio_number(cfg["enable"])

        # Mark pins as used
        pin_step.in_use = True
        pin_forward.in_use = True
        pin_enable.in_use = True

        motor = MotorModel(
            id=cfg["id"],
            name=cfg["name"],
            pin_step=pin_step,
            pin_forward=pin_forward,
            pin_enable=pin_enable,
            start_freq=100,
            target_freq=300,
            total_steps=200,
            duty=50,
            accel_steps=0,
            decel_steps=0,
            loops=10
        )
        db_obj.session.add(motor)

    db_obj.session.commit()
    print("[Motors] Default motors inserted.")