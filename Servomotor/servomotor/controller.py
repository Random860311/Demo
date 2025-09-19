from typing import Optional

import pigpio
import threading

from core.event.event_dispatcher import EventDispatcher
from servomotor.controller_status import EMotorStatus
from servomotor.event.controller_event import MotorStatusData
from servomotor.tracker.position_tracker import PositionTracker


class ControllerPWM:
    def __init__(self,
                 dispatcher: EventDispatcher,
                 pi: pigpio.pi,
                 controller_id: int,
                 current_position: int,
                 pin_step: int,
                 pin_forward: int,
                 pin_enable: int,
                 duty: float = 50):

        """
        Hardware PWM-capable GPIOs on the 40-pin header (Pi 3/4/5):
        GPIO12 (physical pin 32) — PWM0
        GPIO18 (physical pin 12) — PWM0
        GPIO13 (physical pin 33) — PWM1
        GPIO19 (physical pin 35) — PWM1
        """

        self.__event_dispatcher = dispatcher
        self.__pi = pi
        self.__controller_id = controller_id
        self.__pin_step = pin_step
        self.__pin_forward = pin_forward
        self.__pin_enable = pin_enable
        self.__duty = duty

        self.__forward_movement: Optional[bool] = None

        self._freq_table = []
        self._pulses = []

        self.__status = EMotorStatus.STOPPED
        self.__abort_event = threading.Event()

        self.__pi.write(self.__pin_enable, 0)   # ensure initially the service is stopped

        print(f"Initializing tracker for controller {controller_id} with position {current_position}")
        self.__tracker = PositionTracker(current_position=current_position)

    @property
    def pi(self) -> pigpio.pi:
        return self.__pi
    @pi.setter
    def pi(self, value: pigpio.pi):
        self.__pi = value

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
        # emit every 50 ms while RUNNING, but break immediately if aborted
        while self.__status == EMotorStatus.RUNNING:
            # compute current position in memory
            self.__tracker.tick()

            self.__event_dispatcher.emit_async(MotorStatusData(self.__controller_id, self.__status, self.__tracker.get_steps(), self.__forward_movement))

            # interruptible sleep (breaks instantly when stop() sets the event)
            if self.__abort_event.wait(0.01):
                break


    def set_home(self) -> None:
        self.__tracker.set_home()

    def get_position_steps(self) -> int:
        return self.__tracker.get_steps()

    def stop(self) -> bool:
        try:
            # Interrupt the wait if any (case infinite)
            self.__abort_event.set()

            # Disable services
            self.__pi.write(self.__pin_enable, 1)
            self.__pi.hardware_PWM(self.__pin_step, 0, 0)

            # Account actual steps
            self.__tracker.finish_motion()

            if self.status != EMotorStatus.STOPPED:
                # Update controller status
                self.status = EMotorStatus.STOPPED
                self.__forward_movement = None
                self.__event_dispatcher.emit_async(MotorStatusData(self.__controller_id, self.status, self.__tracker.get_steps(), self.__forward_movement))
                return True
            else:
                print(f"Motor {self.__controller_id} already stopped do not emit any event.")
        except Exception as e:
            print(f"Error stopping services: {e}")
            self.status = EMotorStatus.FAULTED
            raise e
        return False

    def run(self, freq_hz: int, forward: bool = True, steps: int = 1):
        if self.status == EMotorStatus.RUNNING:
            print(f"Motor {self.__controller_id} is already running.")
            return
        if freq_hz == 0:
            raise ValueError("Frequency cannot be 0")

        def worker():
            try:
                self.__forward_movement = forward
                self.__abort_event.clear()

                # Enable services
                self.__pi.write(self.__pin_enable, 0)

                # Set direction
                self.__pi.write(self.__pin_forward, 1 if forward else 0)

                # Begin motion context
                self.__tracker.begin_motion(programmed_steps=steps, forward=forward, freq_hz=float(freq_hz))

                #Start running
                result = self.__pi.hardware_PWM(self.__pin_step, int(freq_hz), int(self.duty * 10_000))

                if result != 0:
                    # Something went wrong
                    print(f"Error starting PWM: {self.__controller_id} code: {result}")
                    raise Exception(f"Error starting PWM: {self.__controller_id} code: {result}")

                self.status = EMotorStatus.RUNNING

                # NOT Infinite
                if steps > 0:
                    # Sleep the thread for the calculated duration to move the desired steps
                    duration = steps / freq_hz
                    print(f"Moving motor: {self.__controller_id}, {steps} steps for {duration} seconds")
                    self.__abort_event.wait(duration)
                    self.stop()
                else:
                    print(f"Started infinite movement: {self.__controller_id}")

            except Exception as e:
                print(f"Error running motor: {self.__controller_id} {e}")
                self.status = EMotorStatus.FAULTED
                self.stop()
                raise e

        threading.Thread(target=worker, daemon=True).start()