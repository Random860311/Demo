from core.event.base_event import BaseEvent


class ControllerPWMEvent(BaseEvent[int]):
    def __init__(self, key: str, controller_id: int):
        super().__init__(key=key, data=controller_id)