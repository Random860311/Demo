import pigpio
import threading
from core.event.event_dispatcher import dispatcher
from servomotor.controller_status import MotorStatus
from servomotor.event.controller_pwm_event import ControllerPWMEvent


class ControllerPWM:
    def __init__(self,
                 pi: pigpio.pi,
                 controller_id: int,
                 total_steps: int,
                 target_freq: int,
                 pin_step: int,
                 pin_forward: int,
                 pin_enable: int,
                 duty: float = 50):

        self.__pi = pi
        self.__controller_id = controller_id
        self.__total_steps = total_steps
        self.__target_freq = target_freq
        self.__pin_step = pin_step
        self.__pin_forward = pin_forward
        self.__pin_enable = pin_enable
        self.__duty = duty

        self._freq_table = []
        self._pulses = []

        self.__status = MotorStatus.STOPPED
        self.__abort_event = threading.Event()

        self.__pi.set_mode(self.__pin_step, pigpio.OUTPUT)
        self.__pi.set_mode(self.__pin_forward, pigpio.OUTPUT)
        self.__pi.set_mode(self.__pin_enable, pigpio.OUTPUT)
        self.__pi.write(self.__pin_enable, 0)   # ensure initially the service is stopped

    @property
    def pi(self) -> pigpio.pi:
        return self.__pi
    @pi.setter
    def pi(self, value: pigpio.pi):
        self.__pi = value

    @property
    def total_steps(self) -> int:
        return self.__total_steps
    @total_steps.setter
    def total_steps(self, value: int):
        self.__total_steps = value

    @property
    def target_freq(self) -> int:
        """Target frequency at full speed Hz"""
        return self.__target_freq
    @target_freq.setter
    def target_freq(self, value: int):
        self.__target_freq = value

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
    def pin_enable(self) -> int:
        """GPIO pin for enable"""
        return self.__pin_enable
    @pin_enable.setter
    def pin_enable(self, value: int):
        self.__pin_enable = value

    @property
    def duty(self) -> float:
        """Duty‑cycle (0‑100%, default 50)"""
        return self.__duty
    @duty.setter
    def duty(self, value: float):
        self.__duty = value

    @property
    def status(self) -> str:
        return self.__status

    @status.setter
    def status(self, value: MotorStatus):
        if self.__status == value:
            return
        self.__status = value
        # Notify listeners of status changes
        dispatcher.emit(ControllerPWMEvent(self.__status, self.__controller_id))

    def stop(self):
        try:
            # Interrupt the wait if any (case infinite)
            self.__abort_event.set()

            # Disable services
            self.__pi.write(self.__pin_enable, 1)
            self.__pi.hardware_PWM(self.__pin_step, 0, 0)

            # Update controller status
            self.status = MotorStatus.STOPPED
        except Exception as e:
            print(f"Error stopping services: {e}")
            self.status = MotorStatus.FAULTED
            raise e


    def run(self, forward: bool = True, infinite: bool = False):
        if self.status == MotorStatus.RUNNING:
            return

        def worker():
            try:
                self.__abort_event.clear()
                self.status = MotorStatus.RUNNING

                # Enable services
                self.__pi.write(self.__pin_enable, 0)

                # Set direction
                self.__pi.write(self.__pin_forward, 1 if forward else 0)

                #Start running
                self.__pi.hardware_PWM(self.__pin_step, self.target_freq, int(self.duty * 10_000))

                # If not infinite sleep the thread for the calculated duration to move the desired steps
                # Stop method is called in the finally block
                # If infinite wait until the call to stop is made
                if not infinite:
                    duration = self.total_steps / self.target_freq
                    self.__abort_event.wait(duration)

            except Exception as e:
                print(f"Error running services: {e}")
                self.status = MotorStatus.FAULTED
                # Call the stop method even if the run is infinite
                self.stop()
                raise e
            finally:
                # Wait for the stop called manually if infinite
                if not infinite:
                    self.stop()

        threading.Thread(target=worker, daemon=True).start()