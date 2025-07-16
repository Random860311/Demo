from dto.motor_dto import MotorDto
from db.model.motor_model import MotorModel
from db.model.pin_model import PinModel
from common.converters.pin_converter import pin_model_to_dto

def motor_model_to_dto(motor: MotorModel) -> MotorDto:
    return MotorDto(
        id=motor.id,
        pin_step=pin_model_to_dto(motor.pin_step),
        pin_forward=pin_model_to_dto(motor.pin_forward),
        pin_enable=pin_model_to_dto(motor.pin_enable),
        total_steps=motor.total_steps,
        target_freq=motor.target_freq,
        duty=motor.duty,
        start_freq=motor.start_freq,
        accel_steps=motor.accel_steps,
        decel_steps=motor.decel_steps,
        loops=motor.loops
    )

def motor_dto_to_model(dto: MotorDto) -> MotorModel:
    # Retrieve associated PinModel objects
    pin_step = PinModel.query.get(dto.pin_step.id)
    pin_forward = PinModel.query.get(dto.pin_forward.id)
    pin_enable = PinModel.query.get(dto.pin_enable.id)

    if not (pin_step and pin_forward and pin_enable):
        raise ValueError("One or more pins do not exist in the database")

    # Optionally mark pins as used
    pin_step.in_use = True
    pin_forward.in_use = True
    pin_enable.in_use = True

    motor = MotorModel.query.get(dto.id)
    if not motor:
        motor = MotorModel(id=dto.id)

    motor.name = f"Motor {dto.id}"
    motor.pin_step = pin_step
    motor.pin_forward = pin_forward
    motor.pin_enable = pin_enable
    motor.total_steps = dto.total_steps
    motor.target_freq = dto.target_freq
    motor.duty = dto.duty
    motor.start_freq = dto.start_freq
    motor.accel_steps = dto.accel_steps
    motor.decel_steps = dto.decel_steps
    motor.loops = dto.loops

    return motor

def apply_motor_dto_to_model(model: MotorModel, dto: MotorDto, pins_in_use: bool = True) -> MotorModel:
    # Retrieve the PinModel instances from DB based on dto.pin_x.id
    pin_step = PinModel.query.get(dto.pin_step.id)
    pin_forward = PinModel.query.get(dto.pin_forward.id)
    pin_enable = PinModel.query.get(dto.pin_enable.id)

    if not (pin_step and pin_forward and pin_enable):
        raise ValueError("One or more pins do not exist in the database")

    # Mark new pins as in use
    pin_step.in_use = pins_in_use
    pin_forward.in_use = pins_in_use
    pin_enable.in_use = pins_in_use

    # Apply updates from dto to the existing model
    model.name = f"Motor {dto.id}"
    model.pin_step = pin_step
    model.pin_forward = pin_forward
    model.pin_enable = pin_enable
    model.total_steps = dto.total_steps
    model.target_freq = dto.target_freq
    model.duty = dto.duty
    model.start_freq = dto.start_freq
    model.accel_steps = dto.accel_steps
    model.decel_steps = dto.decel_steps
    model.loops = dto.loops

    return model