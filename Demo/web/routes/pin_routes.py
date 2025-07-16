from flask import Blueprint, jsonify
from services import pin_service

pin_bp = Blueprint("pin_bp", __name__, url_prefix="/pins")

@pin_bp.route("/", methods=["GET"])
def list_all_pins():
    dto_list = pin_service.get_all()
    print(dto_list)
    return jsonify([dto.__dict__ for dto in dto_list])