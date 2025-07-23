from flask import Blueprint, jsonify, request

from services import motor_service
from dto.motor_dto import MotorDto


motor_bp = Blueprint("motor_bp", __name__, url_prefix="/motor")

@motor_bp.route("/", methods=["GET"])
def list_all_motors():
    dto_list = motor_service.get_all()
    return jsonify([dto.__dict__ for dto in dto_list])

@motor_bp.route("", methods=["POST"], strict_slashes=False)
def update_motor():
    try:
        print("Update motor")
        data = request.get_json()
        print("Update motor, data:", data)
        motor = MotorDto.from_dict(data)
        print("Update motor, motor:", motor.__dict__)
        motor_service.update_motor(motor)
        print("Motor updated", motor)
        return jsonify({"message": "Motor received", "motor_id": motor.id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@motor_bp.route("/start/<int:motor_id>", methods=["POST"])
def start_motor(motor_id):
    data = request.get_json(silent=True) or {}  # prevents crash if body is empty or invalid JSON

    direction = data.get("direction", True)  # default to True if not provided

    if not isinstance(direction, bool):
        return jsonify({"error": "'direction' must be a boolean (true/false)."}), 400

    try:
        motor_service.run_motor(motor_id, forward=direction)
        return jsonify({
            "message": f"Motor {motor_id} started successfully.",
            "direction": "forward" if direction else "reverse"
        }), 200
    except KeyError:
        return jsonify({"error": f"Motor {motor_id} not found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@motor_bp.route("/stop/<int:motor_id>", methods=["POST"])
def stop_motor(motor_id):
    try:
        motor_service.stop_motor(motor_id)
        return jsonify({"message": f"Motor {motor_id} stopped successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500