from abc import ABC, abstractmethod


class BaseMotorDao(ABC):
    @abstractmethod
    def update_motor_position(self, motor_id: int, steps: int) -> None:
        pass

    @abstractmethod
    def get_motor_position(self, motor_id: int) -> int:
        pass