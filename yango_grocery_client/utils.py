from typing import Any, Awaitable, Callable, TypeVar, ParamSpec
from functools import wraps
from .exceptions import YangoBadRequest, YangoRequestError
from .constants import ERROR_STATUSES_FOR_RETRY, MAX_RETRIES, SERVICE_NAME, RETRY_DELAY
from logger.logger import get_logger
import asyncio


P = ParamSpec('P')
R = TypeVar('R')

logger = get_logger(SERVICE_NAME)

def retry_request(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        retries = 0

        while True:
            try:
                return await func(*args, **kwargs)
            except (YangoBadRequest, YangoRequestError) as e:
                if e.status in ERROR_STATUSES_FOR_RETRY and retries <= MAX_RETRIES:
                    retries += 1
                    logger.warning(f'Request error {e.status} for {e.url}. {retries} attempt')
                    await asyncio.sleep(RETRY_DELAY)
                    continue

                logger.error(e.message)
                raise e

    return wrapper

class YangoErrorHandler:
    async def process_yango_error(
        self,
        url: str, status: int,
        trace_id: str | None, request_id: str | None,
        response_text: str | None, payload: Any
    ) -> None:
        """
            Inherit this class and implement your own error handler
            This is useful for logging all integration errors separately from other errors
        """
        raise NotImplementedError('YangoErrorHandler is not implemented')
