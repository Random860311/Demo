import time

import pigpio
import threading

from core.di_container import container
from core.event.event_dispatcher import dispatcher
from servomotor.controller_run_mode import EControllerRunMode
from servomotor.controller_status import EMotorStatus
from servomotor.event.controller_event import MotorStatusData
from servomotor.tracker.position_tracker import PositionTracker


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

        self.__status = EMotorStatus.STOPPED
        self.__abort_event = threading.Event()

        self.__pi.set_mode(self.__pin_step, pigpio.OUTPUT)
        self.__pi.set_mode(self.__pin_forward, pigpio.OUTPUT)
        self.__pi.set_mode(self.__pin_enable, pigpio.OUTPUT)
        self.__pi.write(self.__pin_enable, 0)   # ensure initially the service is stopped

        self.__tracker = container.resolve_new(PositionTracker, motor_id=controller_id)

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
    def status(self) -> EMotorStatus:
        return self.__status

    @status.setter
    def status(self, value: EMotorStatus):
        if self.__status == value:
            return
        self.__status = value
        if value == EMotorStatus.RUNNING:
            threading.Thread(target=self.__start_updates, daemon=True).start()

    def __start_updates(self):
        # emit every 500 ms while RUNNING, but break immediately if aborted
        while self.__status == EMotorStatus.RUNNING:
            # compute current position in memory
            self.__tracker.tick()
            dispatcher.emit(MotorStatusData(self.__controller_id, self.__status, self.__tracker.get_steps()))

            # interruptible sleep (breaks instantly when stop() sets the event)
            if self.__abort_event.wait(0.5):
                break


    def set_home(self) -> None:
        self.__tracker.set_home()

    def get_position_steps(self) -> int:
        return self.__tracker.get_steps()

    def stop(self):
        try:
            # Interrupt the wait if any (case infinite)
            self.__abort_event.set()

            # Disable services
            self.__pi.write(self.__pin_enable, 1)
            self.__pi.hardware_PWM(self.__pin_step, 0, 0)

            # Account actual steps
            self.__tracker.finish_motion(save=True)

            # Update controller status
            self.status = EMotorStatus.STOPPED

            dispatcher.emit(MotorStatusData(self.__controller_id, self.status, self.__tracker.get_steps()))
        except Exception as e:
            print(f"Error stopping services: {e}")
            self.status = EMotorStatus.FAULTED
            raise e


    def run(self, forward: bool = True, run_mode: EControllerRunMode = EControllerRunMode.SINGLE_STEP):
        if self.status == EMotorStatus.RUNNING:
            return

        def worker():
            try:
                self.__abort_event.clear()
                self.status = EMotorStatus.RUNNING

                # Enable services
                self.__pi.write(self.__pin_enable, 0)

                # Set direction
                self.__pi.write(self.__pin_forward, 1 if forward else 0)

                match run_mode:
                    case EControllerRunMode.SINGLE_STEP:
                        programmed = 1
                    case EControllerRunMode.CONFIG:
                        programmed = int(self.total_steps)
                    case EControllerRunMode.INFINITE:
                        programmed = 0

                #programmed = 0 if run_mode else int(self.total_steps)  # 0 => unbounded for infinite
                # Begin motion context
                self.__tracker.begin_motion(programmed_steps=programmed, forward=forward, freq_hz=float(self.target_freq))

                #Start running
                result = self.__pi.hardware_PWM(self.__pin_step, self.target_freq, int(self.duty * 10_000))

                if result != 0:
                    # Something went wrong
                    print(f"Error setting PWM: {result}")
                    self.stop()
                    return

                if run_mode != EControllerRunMode.INFINITE:
                    # Sleep the thread for the calculated duration to move the desired steps
                    # Stop method is called in the finally block
                    duration = programmed / self.target_freq
                    print(f"Moving {programmed} steps in {duration} seconds: {self.__controller_id}")
                    self.__abort_event.wait(duration)
                else:
                    print(f"Started infinite movement: {self.__controller_id}")

            except Exception as e:
                print(f"Error running services: {e}")
                self.status = EMotorStatus.FAULTED
                self.stop()
                raise e
            finally:
                # Wait for the stop called manually if infinite
                if run_mode != EControllerRunMode.INFINITE:
                    self.stop()

        threading.Thread(target=worker, daemon=True).start()