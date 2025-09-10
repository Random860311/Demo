from typing import Optional, Any, Mapping

from core.serializable import Serializable


class BaseError(Exception, Serializable):
    """
        Base app/domain error.
        - user_message: safe message for clients
        - detail: internal detail for logs (optional)
        - code: short machine-readable code
        - status_code: int or an enum (e.g., HTTP 4xx/5xx or your EStatusCode)
        - extra: dict with structured context
        """

    def __init__(
            self,
            user_message: str,
            *,
            detail: Optional[str] = None,
            code: Optional[str] = None,
            status_code: Optional[int] = None,
            extra: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(user_message)
        self._user_message = user_message
        self._detail = detail
        self._code = code
        self._status_code = status_code
        self._extra = dict(extra) if extra else {}

    @property
    def user_message(self) -> str:
        return self._user_message
    @property
    def detail(self) -> Optional[str]:
        return self._detail
    @property
    def code(self) -> Optional[str]:
        return self._code
    @property
    def status_code(self) -> Optional[int]:
        return self._status_code
    @property
    def extra(self) -> Mapping[str, Any]:
        return self._extra

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code}, msg={self.user_message})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "message": self.user_message,
            "code": self.code,
            "extra": self.extra or None,
        }