from typing import Any


class YangoException(Exception):
    pass


class YangoRequestError(YangoException):
    def __init__(
        self, message: str, url: str, status: int, response_text: str, payload: dict[Any, Any] | None = None
    ) -> None:
        self.message = message
        self.response_text = response_text
        self.status = status
        self.url = url
        self.payload = payload if payload is not None else {}

        super().__init__(message)
