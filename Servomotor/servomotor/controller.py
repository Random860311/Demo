import pigpio
import time
from . import utils, common
import threading

class ControllerPWM:
    def __init__(self,
                 pi: pigpio.pi,
                 total_steps: int,
                 target_freq: int,
                 pin_step: int,
                 pin_forward: int,
                 pin_enable: int,
                 duty: float = 50,
                 start_freq: int = 500,
                 accel_steps: int = 0,
                 decel_steps: int = 0):
        """
        1- The user supplies required parameters at runtime, including pi instance.
        2- Acceleration / deceleration: Linear ramps are produced by inserting gradually changing frequencies into the pulse train.
           Adjust accel_steps and decel_steps independently (set to 0 for no ramp).
        3- Each step = HIGH+LOW transition. Builds one pigpio waveform containing exactly total_steps × 2 pulses.
        5- Duty‑cycle: For each period the HIGH time is period × duty%, LOW = remainder.
        6- Limits & Safety: pigpio needs ≥ 1µs per pulse; the script throws an error if you exceed that.
           Waveforms use DMA RAM; extremely large total_steps (hundreds of thousands) might exhaust memory
           Only GPIO 12, 13, 18,19 are tied to the on-chip PWM hardware; they give the cleanest edges at high speed.

        :param pi: pigpio.pi instance
        :param total_steps: Total number of steps (pulses). Complete pulses (HIGH and LOW) that will be generated

                            Example:
                            total_steps = 3
                            Frequency = 1000 Hz → period = 1000µs
                            Duty = 50% → HIGH = 500 µs, LOW = 500µs
                            |––500µs–HIGH––|––500µs–LOW––|––500µs–HIGH––|––500µs–LOW––|––500µs–HIGH––|––500µs–LOW––|
                                Step 1                          Step 2                      Step 3

        :param target_freq: Target frequency at full speed Hz. It defines how fast the pulses are sent,
                            and therefore how fast the services or device moves once at full speed.

                            Example:
                            | `target_freq` | Period (1 step) | Description              |
                            | ------------- | --------------- | ------------------------ |
                            | 1000 Hz       | 1000 µs         | 1 step every millisecond |
                            | 2000 Hz       | 500 µs          | Faster steps             |
                            | 100 Hz        | 10,000 µs       | Slower steps             |

        :param pin_step: GPIO pin for STEP (12, 13, 18 or 19 recommended)
        :param pin_forward: GPIO pin for FORWARD (maintained signal while in movement)
        :param pin_enable: GPIO pin for enable
        :param duty: Duty‑cycle (0‑100%, default 50). Duty (%) = (Time the signal is HIGH / Total period of one cycle) × 100

                     | Duty Cycle | High Time (ON) | Low Time (OFF) | What It Looks Like       |
                     | ---------- | -------------- | -------------- | ------------------------ |
                     | 50%        | 500 µs         | 500 µs         | Equal ON/OFF square wave |
                     | 25%        | 250 µs         | 750 µs         | Short pulses, long off   |
                     | 75%        | 750 µs         | 250 µs         | Long pulses, short off   |
                     | 100%       | 1000 µs        | 0 µs           | Always ON (no OFF time)  |
                     | 0%         | 0 µs           | 1000 µs        | Always OFF (no ON time)  |

                     | Application                      | Effect of Duty Cycle                       |
                     | -------------------------------- | ------------------------------------------ |
                     | LED brightness                   | Higher duty = brighter light               |
                     | Motor speed (PWM control)        | Higher duty = faster services rotation        |
                     | Servo pulses (if fixed freq)     | Duty maps to position (e.g., 1–2ms pulses) |
                     | Stepper/servo pulse trains       | Often kept at 50% to match driver specs    |

        :param start_freq:  Start frequency for ramp‑up [Hz] (default 500)

                            If generating total_steps = 1000 with acceleration and deceleration, your motion will look like this:
                                      Frequency
                                          ▲
                            target_freq ─────────────────────┐
                                        ╱                    │
                                       ╱                     │
                            start_freq ───────────────╲──────┘
                                                      Step Count ➝
                                   accel_steps     constant     decel_steps

                            Example:
                                start_freq = 200 Hz → 5 ms per step (1000 ms / 200)
                                target_freq = 1000 Hz → 1 ms per step
                                accel_steps = 200
                            Then for the first 200 steps:
                                Step 1 is at 5 ms
                                Step 200 is at 1 ms
                                Each step in between is interpolated

        :param accel_steps: Steps used to speed up (default 0 = no ramp)
        :param decel_steps: Steps used to decelerate (default 0 = no ramp)
        """
        self.__pi = pi
        self.__total_steps = total_steps
        self.__target_freq = target_freq
        self.__pin_step = pin_step
        self.__pin_forward = pin_forward
        self.__pin_enable = pin_enable
        self.__duty = duty
        self.__start_freq = start_freq
        self.__accel_steps = accel_steps
        self.__decel_steps = decel_steps

        self._freq_table = []
        self._pulses = []

        self.__lock = threading.Lock()
        self.__status = common.MotorStatus.STOPPED

        if not self.__pi.connected:
            raise RuntimeError("pigpiod daemon not running. Start with 'sudo pigpiod' \nor make sure: \n sudo systemctl enable pigpiod \nsudo systemctl start pigpiod")

        if self.__pin_step == self.__pin_forward:
            raise RuntimeError("pins must be different")

        self.__pi.set_mode(self.__pin_step, pigpio.OUTPUT)
        self.__pi.set_mode(self.__pin_forward, pigpio.OUTPUT)
        self.__pi.set_mode(self.__pin_enable, pigpio.OUTPUT)
        self.__pi.write(self.__pin_enable, 0)   # ensure initially the services is stopped

        try:
            self.__wave_id = utils.create_ramp_waveform(
                pi=self.__pi,
                accel_steps=self.accel_steps,
                decel_steps=self.decel_steps,
                total_steps=self.total_steps,
                target_freq=self.target_freq,
                start_freq=self.start_freq,
                pin_step=self.pin_step,
                duty=self.duty,
            )
        except Exception as e:
            self.__wave_id = pigpio.PI_NO_WAVEFORM_ID
            print(f"Error creating ramp waveform in constructor: {e}")


        # self.__pi.set_pull_up_down(self.__pin_step, pigpio.PUD_UP)
        # self.__pi.set_pull_up_down(self.__pin_forward, pigpio.PUD_UP)
        # self.__pi.set_pull_up_down(self.__pin_reverse, pigpio.PUD_UP)

    def _invalidate_wave(self):
        if self.__wave_id != pigpio.PI_NO_WAVEFORM_ID:
            self.__pi.wave_delete(self.__wave_id)
            self.__wave_id = pigpio.PI_NO_WAVEFORM_ID

    @property
    def total_steps(self) -> int:
        """Total number of steps (pulses)"""
        return self.__total_steps
    @total_steps.setter
    def total_steps(self, value: int):
        self.__total_steps = value
        self._invalidate_wave()

    @property
    def target_freq(self) -> int:
        """Target frequency at full speed Hz"""
        return self.__target_freq
    @target_freq.setter
    def target_freq(self, value: int):
        self.__target_freq = value
        self._invalidate_wave()

    @property
    def pin_step(self) -> int:
        """GPIO pin for STEP (12, 13, 18 or 19 recommended)"""
        return self.__pin_step
    @pin_step.setter
    def pin_step(self, value: int):
        self.__pin_step = value

    @property
    def pin_forward(self) -> int:
        """GPIO pin for FORWARD"""
        return self.__pin_forward
    @pin_forward.setter
    def pin_forward(self, value: int):
        self.__pin_forward = value

    @property
    def duty(self) -> float:
        """Duty‑cycle (0‑100%, default 50)"""
        return self.__duty
    @duty.setter
    def duty(self, value: float):
        self.__duty = value
        self._invalidate_wave()

    @property
    def start_freq(self) -> int:
        """Start frequency for ramp‑up [Hz] (default 500)"""
        return self.__start_freq
    @start_freq.setter
    def start_freq(self, value: int):
        self.__start_freq = value
        self._invalidate_wave()

    @property
    def accel_steps(self) -> int:
        """Steps used to speed up (default 0 = no ramp)"""
        return self.__accel_steps
    @accel_steps.setter
    def accel_steps(self, value: int):
        self.__accel_steps = value
        self._invalidate_wave()

    @property
    def decel_steps(self) -> int:
        """Steps used to decelerate (default 0 = no ramp)"""
        return self.__decel_steps
    @decel_steps.setter
    def decel_steps(self, value: int):
        self.__decel_steps = value
        self._invalidate_wave()

    @property
    def status(self) -> common.MotorStatus:
        return self.__status

    def stop(self):
        self.__status = common.MotorStatus.STOPPED
        # Disable services
        self.__pi.write(self.__pin_enable, 1)
        self.__pi.wave_delete(self.__wave_id)
        self.__wave_id = pigpio.PI_NO_WAVEFORM_ID

    def run(self, forward: bool = True):
        with self.__lock:
            try:
                if self.__status == common.MotorStatus.RUNNING:
                    return
                self.__status = common.MotorStatus.RUNNING

                # Enable services
                self.__pi.write(self.__pin_enable, 0)

                # Set direction
                self.__pi.write(self.__pin_forward, 1 if forward else 0)

                if self.__wave_id == pigpio.PI_NO_WAVEFORM_ID:
                    self.__wave_id = utils.create_ramp_waveform(
                        pi=self.__pi,
                        accel_steps=self.accel_steps,
                        decel_steps=self.decel_steps,
                        total_steps=self.total_steps,
                        target_freq=self.target_freq,
                        start_freq=self.start_freq,
                        pin_step=self.pin_step,
                        duty=self.duty,
                    )

                print(f"\nStarting motion. "
                      f"WaveId: {self.__wave_id} "
                      f"Pins used: Wave: {self.__pin_step}, "
                      f"Forward: {self.__pin_forward} "
                      f"Total steps: {self.__total_steps} "
                  )
                self.__pi.wave_send_once(self.__wave_id)


                print("Motion finished.")
                self.__status = common.MotorStatus.STOPPED
                #self.stop()
            except Exception as e:
                self.stop()
                print(f"Error running services: {e}")