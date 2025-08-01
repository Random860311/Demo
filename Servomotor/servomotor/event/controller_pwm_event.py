from core.event.base_event import BaseEvent


class ControllerPWMEvent(BaseEvent[int]):
    def __init__(self, event_name: str, controller_id: int):
        super().__init__(event_name=event_name, data=controller_id)