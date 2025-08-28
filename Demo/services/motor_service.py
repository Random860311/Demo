from typing import Optional
from core.event.event_dispatcher import EventDispatcher
from db.dao.motor_dao import MotorDao
from servomotor.controller_run_mode import EControllerRunMode
from servomotor.controller_status import EMotorStatus
from servomotor.event.controller_event import MotorStatusData
from web.events.motor_event import MotorUpdatedEvent
from common.converters import motor_converter
from common.converters.motor_converter import motor_model_to_dto

from dto.motor_dto import MotorDto
from .base_service import BaseService
from .pigpio_service import PigpioService


class MotorService(BaseService):

    def __init__(self, dispatcher: EventDispatcher, pigpio: PigpioService, motor_dao: MotorDao):
        super().__init__(dispatcher)

        self.__pigpio_service = pigpio
        self.__motor_dao = motor_dao

        self._subscribe_to_events()

    def get_all(self) -> list[MotorDto]:
        motor_models = self.__motor_dao.get_all()
        motor_dtos: list[MotorDto]= []

        for motor_model in motor_models:
            dto = motor_model_to_dto(motor_model)
            # dto.status = self.get_motor_status(motor_model.id)
            motor_dtos.append(dto)

        return motor_dtos

    def get_motor(self, motor_id: int) -> Optional[MotorDto]:
        motor_model = self.__motor_dao.get_by_id(motor_id)
        motor_dto = motor_model_to_dto(motor_model) if motor_model else None
        motor_dto.status = self.get_motor_status(motor_id)

        return motor_dto

    def get_motor_status(self, motor_id: int) -> EMotorStatus:
        return self.__pigpio_service.get_controller_status(motor_id)

    def run_motor(self, motor_id: int, forward: bool = True, run_mode: EControllerRunMode = EControllerRunMode.SINGLE_STEP):
        controller = self.__pigpio_service.get_controller(motor_id)
        print(f"MotorService run_motor: {motor_id} forward: {forward} run_mode: {run_mode}")
        controller.run(forward=forward, run_mode=run_mode)

    def stop_motor(self, motor_id: int):
        controller = self.__pigpio_service.get_controller(motor_id)
        controller.stop()

    def update_motor(self, motor_dto: MotorDto) -> MotorDto:
        existing_motor_model = self.__motor_dao.get_by_id(motor_dto.id)
        motor_converter.motor_dto_to_model(motor_dto, existing_motor_model)

        self.__motor_dao.update_motor(existing_motor_model)
        self.__pigpio_service.update_controller(motor_dto)
        self._dispatcher.emit_async(MotorUpdatedEvent(motor_dto))
        print(f"MotorService update_motor: {motor_dto.id}, {motor_dto.position}")
        return motor_dto

    def _handle_controller_status_change(self, event: MotorStatusData):
        motor_dto = self.get_motor(event.motor_id)
        motor_dto.status = event.status
        motor_dto.position = event.position
        self.__motor_dao.update_motor_position(event.motor_id, event.position)
        self._dispatcher.emit_async(MotorUpdatedEvent(motor_dto))

        print(f"MotorService _handle_controller_status_change: {motor_dto.id}, {motor_dto.position}")

    def _subscribe_to_events(self):
        self._dispatcher.subscribe(MotorStatusData, self._handle_controller_status_change)

