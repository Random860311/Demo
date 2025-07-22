from flask import Blueprint, jsonify
from services import pin_service

pin_bp = Blueprint("pin_bp", __name__, url_prefix="/pin")

@pin_bp.route("/", methods=["GET"])
def list_all_pins():
    dto_list = pin_service.get_all()
    return jsonify([dto.__dict__ for dto in dto_list])

@pin_bp.route("/available", methods=["GET"])
def list_available_pins():
    dto_list = pin_service.get_available_pins()
    return jsonify([dto.__dict__ for dto in dto_list])