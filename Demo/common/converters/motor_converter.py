from dto.motor_dto import MotorDto
from db.model.motor_model import MotorModel
from common.converters.pin_converter import pin_model_to_dto

def motor_model_to_dto(motor_model: MotorModel) -> MotorDto:
    motor_dto=MotorDto(
        id=motor_model.id,
        name=motor_model.name,
        pin_step=None,
        pin_forward=None,
        pin_enable=None,
        angle=motor_model.angle,
        target_freq=motor_model.target_freq,
        duty=motor_model.duty,

        turns=motor_model.turns,
        distance=motor_model.distance,
        distance_per_turn=motor_model.distance_per_turn,
        position=motor_model.position,

    )
    if motor_model.pin_step:
        motor_dto.pin_step = pin_model_to_dto(motor_model.pin_step)
    if motor_model.pin_forward:
        motor_dto.pin_forward = pin_model_to_dto(motor_model.pin_forward)
    if motor_model.pin_enable:
        motor_dto.pin_enable = pin_model_to_dto(motor_model.pin_enable)
    return motor_dto

def motor_dto_to_model(dto: MotorDto, motor_model: MotorModel):
    motor_model.name = dto.name if dto.name else f"Motor {dto.id}"
    motor_model.target_freq = dto.target_freq
    motor_model.angle = dto.angle
    motor_model.duty = dto.duty
    motor_model.turns = dto.turns
    motor_model.distance = dto.distance
    motor_model.distance_per_turn = dto.distance_per_turn
    motor_model.position = dto.position

    return motor_model

