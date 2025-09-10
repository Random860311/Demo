from typing import Optional

from core.error.base_error import BaseError
from web.events.response import EStatusCode


class AppWarning(BaseError):
    def __init__(self, message: str):
        super().__init__(message, code=EStatusCode.WARNING)

    @property
    def code(self) -> EStatusCode:
        return EStatusCode.from_value(self._code)