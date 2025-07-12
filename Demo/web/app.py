from flask import Flask, jsonify
import pigpio
from servomotor import controller
app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "API is running"})

@app.route("/status")
def status():
    pi = pigpio.pi()

    driver = controller.ControllerPWM(
        pi=pi,
        target_freq=300,
        total_steps=200,
        pin_step=12,
        pin_forward=16,

        duty=50,
        start_freq=0,
        accel_steps=0,
        decel_steps=0,
        loops=10
    )
    driver.run()

    return jsonify({"status": "ok"})

