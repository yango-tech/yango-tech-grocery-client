from typing import Any


class YangoException(Exception):
    pass


class YangoRequestError(YangoException):
    def __init__(self, message: str, url: str, status: int) -> None:
        self.message = message
        self.status = status
        self.url = url

        super().__init__(message)


class YangoBadRequest(YangoRequestError):
    def __init__(self, message: str, url: str, status: int, payload: dict[Any, Any]) -> None:
        self.payload = payload

        super().__init__(message, url, status)
