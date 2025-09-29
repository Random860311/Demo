from typing import Optional, Unpack

import pigpio

from core.event.event_dispatcher import EventDispatcher
from core.thread_manager import ThreadManagerProtocol
from servomotor.controller.base_controller import BaseController
from servomotor.controller.controller_protocol import RunKwargs
from servomotor.dto.controller_status import EMotorStatus
from servomotor.event.controller_event import ControllerStatusEvent


class SinglePWMController(BaseController):
    def __init__(self,
                 dispatcher: EventDispatcher,
                 thread_manager: ThreadManagerProtocol,
                 pi: pigpio.pi,
                 controller_id: int,
                 pin_step: int,
                 pin_forward: int,
                 pin_enable: int):
        super().__init__(dispatcher, pi, thread_manager)

        """
        Hardware PWM-capable GPIOs on the 40-pin header (Pi 3/4/5):
        GPIO12 (physical pin 32) — PWM0
        GPIO18 (physical pin 12) — PWM0
        GPIO13 (physical pin 33) — PWM1
        GPIO19 (physical pin 35) — PWM1
        """
        self.__controller_id = controller_id
        self.__pin_step = pin_step
        self.__pin_forward = pin_forward
        self.__pin_enable = pin_enable
        self.__run_freq_hz = 0

        self.__forward_movement: Optional[bool] = None

        self.pi.write(self.__pin_enable, 0)   # ensure initially the service is stopped

    def _emit_status_update(self):
        self._event_dispatcher.emit_async(ControllerStatusEvent(
            motor_id=self.__controller_id,
            status=self.__status,
            freq_hz=self.__run_freq_hz,
            direction=self.__forward_movement)
        )

    def is_motor_in_use(self, motor_id: int) -> bool:
        return self.__controller_id == motor_id

    def stop(self) -> bool:
        try:
            # Disable services
            self.pi.set_PWM_dutycycle(int(self.__pin_step), 0)
            self.pi.write(self.__pin_enable, 1)
            # self.__pi.hardware_PWM(self.__pin_step, 0, 0)

            # Interrupt the wait if any (case infinite)
            self._abort_event.set()
            self.__run_freq_hz = 0

            if self.status != EMotorStatus.STOPPED:
                # Update controller status
                self.status = EMotorStatus.STOPPED
                self.__forward_movement = None
                return True
        except Exception as e:
            print(f"Error stopping services: {e}")
            raise e
        return False

    def run(self, **kwargs: Unpack[RunKwargs]):
        if self.status == EMotorStatus.RUNNING:
            print(f"Motor {self.__controller_id} is already running.")
            return

        freq_hz = kwargs.get("freq_hz", 0)
        direction = kwargs.get("direction", True)
        steps = kwargs.get("steps", 1)
        duty = kwargs.get("duty", 50)

        if freq_hz == 0:
            raise ValueError("Frequency cannot be 0")

        def worker():
            try:
                self.__run_freq_hz = freq_hz
                self.__forward_movement = direction
                self._abort_event.clear()

                # Enable services
                self.pi.write(self.__pin_enable, 0)

                # Set direction
                self.pi.write(self.__pin_forward, 1 if direction else 0)

                #Start running
                print(f"Starting motor: {self.__controller_id} at {freq_hz} Hz for {steps} steps, pin used: {self.__pin_step}")

                # result = self.__pi.hardware_PWM(self.__pin_step, int(freq_hz), int(self.duty * 10_000))

                self.pi.set_PWM_frequency(int(self.__pin_step), int(freq_hz))
                result = self.pi.set_PWM_dutycycle(int(self.__pin_step), duty)

                if result != 0:
                    # Something went wrong
                    print(f"Error starting PWM: {self.__controller_id} code: {result}")
                    raise Exception(f"Error starting PWM: {self.__controller_id} code: {result}")

                self.status = EMotorStatus.RUNNING

                # NOT Infinite
                if steps > 0:
                    # Sleep the thread for the calculated duration to move the desired steps
                    duration = steps / freq_hz
                    # print(f"Moving motor: {self.__controller_id}, {steps} steps for {duration} seconds")
                    self._abort_event.wait(duration)
                    self.stop()
                else:
                    print(f"Started infinite movement: {self.__controller_id}")

            except Exception as e:
                print(f"Error running motor: {self.__controller_id} {e}")
                self.stop()
                raise e
        self._thread_manager.start_background_task(worker)
        # threading.Thread(target=worker, daemon=True).start()