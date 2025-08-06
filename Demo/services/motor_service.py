from typing import Optional
from core.event.event_dispatcher import EventDispatcher
from db.dao.motor_dao import MotorDao
from servomotor.controller_status import MotorStatus
from servomotor.event.controller_pwm_event import ControllerPWMEvent
from web.events.motor_event import MotorUpdatedEvent, MotorStatusChangedEvent
from . import pigpio_service
from common.converters import motor_converter
from common.converters.motor_converter import motor_model_to_dto

from dto.motor_dto import MotorDto
from .base_service import BaseService


class MotorService(BaseService):

    def __init__(self, dispatcher: EventDispatcher, pigpio: pigpio_service.PigpioService, motor_dao: MotorDao):
        super().__init__(dispatcher)

        self.__pigpio_service = pigpio
        self.__motor_dao = motor_dao

        self._subscribe_to_events()

    @staticmethod
    def get_all() -> list[MotorDto]:
        motor_models = MotorDao.get_all()
        return [motor_model_to_dto(motor_model) for motor_model in motor_models]

    @staticmethod
    def get_motor(motor_id: int) -> Optional[MotorDto]:
        motor_model = MotorDao.get_by_id(motor_id)
        return motor_model_to_dto(motor_model) if motor_model else None

    def get_motor_status(self, motor_id: int) -> str:
        controller = self.__pigpio_service.get_controller(motor_id)
        return controller.status

    def run_motor(self, motor_id: int, forward: bool = True, infinite: bool = False):
        controller = self.__pigpio_service.get_controller(motor_id)
        controller.run(forward=forward, infinite=infinite)

    def stop_motor(self, motor_id: int):
        controller = self.__pigpio_service.get_controller(motor_id)
        controller.stop()

    def update_motor(self, motor_dto: MotorDto) -> MotorDto:
        existing_motor_model = MotorDao.get_by_id(motor_dto.id)
        motor_converter.motor_dto_to_model(motor_dto, existing_motor_model)
        self.__motor_dao.update_motor(existing_motor_model)

        self._dispatcher.emit(MotorUpdatedEvent(motor_dto))

        return motor_dto

    def _handle_controller_status_change(self, event: ControllerPWMEvent):
        print("MotorService: _handle_controller_status_change:", event.__dict__)
        self._dispatcher.emit(MotorStatusChangedEvent(motor_id=event.data, status=event.key))

    def _subscribe_to_events(self):
        self._dispatcher.subscribe(ControllerPWMEvent, self._handle_controller_status_change)

