from collections.abc import Generator
from enum import Enum
from typing import Any, TypeVar

import aiohttp
from aiohttp import ClientSession
from yarl import URL

from .constants import DEFAULT_BATCH_SIZE
from .exceptions import YangoRequestError
from .rate_limiter import yango_rate_limiter
from .utils import YangoErrorHandler, retry_request

T = TypeVar('T')


class BaseYangoClient:
    def __init__(
        self,
        domain: str,
        auth_token: str,
        error_handler: YangoErrorHandler | None = None,
        proxy: str | URL | None = None,
        ssl: bool | None = None,
        should_use_rate_limiter: bool = False,
    ):
        self.auth_token = auth_token
        self.domain = domain
        self.error_handler = error_handler
        self.proxy = proxy
        self.ssl = ssl if ssl is not None else not bool(proxy)
        self.should_use_rate_limiter = should_use_rate_limiter

    async def process_yango_response(self, resp: aiohttp.ClientResponse, payload: dict[Any, Any] | None = None) -> Any:
        trace_id = resp.headers.get('x-yatraceid')
        request_id = resp.headers.get('x-yarequestid')
        status = resp.status

        if 200 <= status < 300:
            return await resp.json()

        url = str(resp.url)
        response_text = await resp.text()

        message = (
            f'Status {status} from Yango on {url}. Trace ID {trace_id}.'
            f'Request ID {request_id}. Response {response_text}'
        )
        if self.error_handler is not None:
            await self.error_handler.process_yango_error(
                url, status, trace_id, request_id, response_text, payload=payload
            )

        raise YangoRequestError(message, url, status, response_text, payload=payload)

    @retry_request
    async def yango_request(self, endpoint: str, data: dict[str, Any]) -> Any:
        if self.should_use_rate_limiter:
            await yango_rate_limiter.acquire(endpoint, auth_token=self.auth_token)

        headers = {'Authorization': f'Bearer {self.auth_token}', 'Content-Type': 'application/json'}
        url = self.domain + endpoint
        async with ClientSession() as session:
            async with session.post(url=url, json=data, headers=headers, proxy=self.proxy, ssl=self.ssl) as resp:
                return await self.process_yango_response(resp, payload=data)

    @retry_request
    async def yango_multipart_request(self, endpoint: str, data: dict[str, Any]) -> Any:
        if self.should_use_rate_limiter:
            await yango_rate_limiter.acquire(endpoint, auth_token=self.auth_token)

        headers = {'Authorization': f'Bearer {self.auth_token}'}
        url = self.domain + endpoint
        form_data = aiohttp.FormData()
        for key, value in data.items():
            if isinstance(value, int):
                value = str(value)
            if isinstance(value, Enum):
                value = value.value
            form_data.add_field(name=key, value=value)

        async with ClientSession() as session:
            async with session.post(url=url, data=form_data, headers=headers, proxy=self.proxy, ssl=self.ssl) as resp:
                return await self.process_yango_response(resp)

    @staticmethod
    def batch_items(items: list[T], batch_size: int = DEFAULT_BATCH_SIZE) -> Generator[list[T], None, None]:
        for i in range(0, len(items), batch_size):
            yield items[i : i + batch_size]
