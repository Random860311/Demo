from flask import Blueprint, jsonify, request

from services import pin_service
from servomotor.controller import ControllerPWM
from dto.motor_dto import MotorDto
from dto.pin_dto import PinDto


motor_routes = Blueprint("motor_routes", __name__)

# Shared services pool
motor_pool: dict[int, ControllerPWM] = {}

@motor_routes.route("/motors/update", methods=["POST"])
def update_motor():
    try:
        moto = request.get_json()
        configs = MotorDto.from_list(data)

        # Validate unique GPIOs
        all_pins = set()
        for config in configs:
            pins = (config.pin_step, config.pin_forward, config.pin_enable)
            if any(p in all_pins for p in pins):
                return jsonify({"error": f"GPIO pin conflict in services ID {config.id}"}), 400
            all_pins.update(pins)

        # Rebuild motor_pool
        motor_pool.clear()
        for cfg in configs:
            motor_pool[cfg.id] = ControllerPWM(
                pi=pigpio_service.pi,
                total_steps=cfg.total_steps,
                target_freq=cfg.target_freq,
                pin_step=cfg.pin_step,
                pin_forward=cfg.pin_forward,
                pin_enable=cfg.pin_enable,
                duty=cfg.duty,
                start_freq=cfg.start_freq,
                accel_steps=cfg.accel_steps,
                decel_steps=cfg.decel_steps,
                loops=cfg.loops
            )

        return jsonify({"message": f"{len(configs)} motors configured."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@motor_routes.route("/motor/<int:motor_id>/run", methods=["POST"])
def run_motor(motor_id):
    try:
        forward = request.args.get("forward", "true").lower() == "true"
        motor = motor_pool.get(motor_id)
        if motor is None:
            return jsonify({"error": "Motor not found"}), 404

        import asyncio
        asyncio.create_task(motor.run(forward=forward))
        return jsonify({"message": f"Motor {motor_id} started."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@motor_routes.route("/motor/<int:motor_id>/stop", methods=["POST"])
def stop_motor(motor_id):
    try:
        motor = motor_pool.get(motor_id)
        if motor is None:
            return jsonify({"error": "Motor not found"}), 404

        import asyncio
        asyncio.create_task(motor.stop())
        return jsonify({"message": f"Motor {motor_id} stopped."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@motor_routes.route("/motor/<int:motor_id>/status", methods=["GET"])
def motor_status(motor_id):
    try:
        motor = motor_pool.get(motor_id)
        if motor is None:
            return jsonify({"error": "Motor not found"}), 404

        return jsonify({"status": motor.status.value})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_motor_dto_from_request() -> MotorDto:
    data = request.get_json()

    def build_pin_dto(pin_data: dict) -> PinDto:
        return PinDto(
            id=pin_data["id"],
            physical_pin_number=pin_data["physical_pin_number"],
            pigpio_pin_number=pin_data.get("pigpio_pin_number"),
            pin_type=PinType(pin_data["pin_type"]),
            description=pin_data["description"],
            in_use=pin_data["in_use"]
        )

    return MotorDto(
        id=data["id"],
        pin_step=build_pin_dto(data["pin_step"]),
        pin_forward=build_pin_dto(data["pin_forward"]),
        pin_enable=build_pin_dto(data["pin_enable"]),
        total_steps=data["total_steps"],
        target_freq=data["target_freq"],
        duty=data["duty"],
        start_freq=data["start_freq"],
        accel_steps=data["accel_steps"],
        decel_steps=data["decel_steps"],
        loops=data["loops"]
    )