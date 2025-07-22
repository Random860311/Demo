from flask import Flask, jsonify
from flask_cors import CORS
import pigpio
from servomotor import controller
from db.model import db_config

from web.routes import pin_routes, motor_routes

app = Flask(__name__)
CORS(app)
app.register_blueprint(pin_routes.pin_bp)
app.register_blueprint(motor_routes.motor_bp)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///demo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db_config.db_obj.init_app(app)

@app.before_request
def create_tables():
    db_config.initialize()

@app.route("/")
def home():
    return jsonify({"message": "API is running"})

# @app.route("/status")
# def status():
#     pi = pigpio.pi()
#
#     driver = controller.ControllerPWM(
#         pi=pi,
#         target_freq=300,
#         total_steps=200,
#         pin_step=12,
#         pin_forward=16,
#         pin_enable=20,
#         duty=50,
#         start_freq=0,
#         accel_steps=0,
#         decel_steps=0,
#         loops=10
#     )
#     driver.run()
#
#     return jsonify({"status": "ok"})

