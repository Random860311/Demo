def calculate_motor_steps_per_turn(motor_angle: float) -> int:
    return 0 if motor_angle <= 0 else round(360 / motor_angle)

def calculate_motor_total_steps(motor_angle: float, distance: float, distance_per_turn: float) -> int:
    if motor_angle <= 0 or distance <= 0 or distance_per_turn <= 0:
        return 0
    turns = calculate_motor_total_turns(distance=distance, distance_per_turn=distance_per_turn)
    steps_per_turn = calculate_motor_steps_per_turn(motor_angle=motor_angle)

    return round(steps_per_turn * turns)

def calculate_motor_total_turns(distance: float, distance_per_turn: float)-> float:
    return 0 if (distance <= 0 or distance_per_turn <= 0) else distance / distance_per_turn