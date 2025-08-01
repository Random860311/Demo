def calculate_motor_total_steps(motor_angle: float, turns: float) -> int:
    return 0 if motor_angle <= 0 else round((360 / motor_angle) * turns)

def calculate_motor_total_turns(turns: float, distance: float = 0, distance_per_turn: float = 0)-> float:
    return turns if (distance <= 0 or distance_per_turn <= 0) else distance / distance_per_turn