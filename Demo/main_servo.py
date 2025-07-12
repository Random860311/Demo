# import sys
# sys.path.append('/home/amed/Desktop/WorkSpace/Servomotor/servomotor')
import asyncio
import pigpio
from servomotor import controller

async def main():
    params = read_params()
    pi = pigpio.pi()

    driver = controller.ControllerPWM(
        pi=pi,
        target_freq=params['target_freq'],
        total_steps=params['total_steps'] or 200,
        pin_step=params['gpio_pin'],
        pin_forward=params['gpio_pin_forward'],
        pin_enable=22,
        duty=params['duty_cycle'],
        start_freq=params.get('start_freq') or 0,
        accel_steps=params['accel_steps'],
        decel_steps=params['decel_steps'],
        loops=params['loops']
    )
    await driver.run()
    await driver.run()
    print("Done!")

def read_params():
    """Query the user for all required motion parameters."""
    params = {}
    # Mandatory -------------------------------------------------------------
    params["target_freq"] = int(input("Target frequency at full speed [Hz]: "))
    params["gpio_pin"] = int(input("GPIO pin for STEP (12, 13, 18 or 19 recommended) (default 12): ") or 12)
    params["gpio_pin_forward"] = int(input("GPIO pin to indicate forward movement (16 default): ") or 16)
    params["total_steps"] = int(input("Total number of steps (pulses) (2000 default): ") or 2000)

    # Optional with sensible defaults ---------------------------------------
    params["duty_cycle"] = float(input("Duty‑cycle (0‑100%, default 50): ") or 50)
    params["accel_steps"] = int(input("Steps used to accelerate (default 0 = no ramp): ") or 0)
    if params["accel_steps"] > 0:
        params["start_freq"] = int(input("Start frequency for ramp‑up [Hz] (default 500): ") or 500)
    params["decel_steps"] = int(input("Steps used to decelerate (default 0 = no ramp): ") or 0)
    params["loops"] = int(input("How many times to repeat the whole sequence? (default 1): ") or 1)
    return params

if __name__ == '__main__':
    # main()
    asyncio.run(main())