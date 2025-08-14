import aiohttp
import json
from aiohttp import ClientSession
from typing import Any
from enum import Enum
from yarl import URL

from .utils import YangoErrorHandler, retry_request
from .exceptions import YangoBadRequest, YangoRequestError


class BaseYangoClient:

    def __init__(
        self,
        domain: str,
        auth_token: str,
        error_handler: YangoErrorHandler | None = None,
        proxy: str | URL | None = None
    ):
        self.auth_token = auth_token
        self.domain = domain
        self.error_handler = error_handler
        self.proxy = proxy
        self.ssl = not bool(proxy)


    async def process_yango_response(self, resp: aiohttp.ClientResponse, payload: dict[str, Any] | None = None) -> Any:
        trace_id = resp.headers.get('x-yatraceid')
        request_id = resp.headers.get('x-yarequestid')
        status = resp.status

        if 200 <= status < 300:
            return await resp.json()

        url = str(resp.url)
        resp_text = await resp.text()

        message = f'Status {status} from Yango on {url}. Trace ID {trace_id}. Request ID {request_id}. Response {resp_text}'
        if self.error_handler is not None:
            await self.error_handler.process_yango_error(
                url, status, trace_id, request_id, resp_text,
                payload=payload
            )

        if status == 400:
            raise YangoBadRequest(message, url, status, payload=json.loads(resp_text))

        raise YangoRequestError(message, url, status)

    @retry_request
    async def yango_request(self, endpoint: str, data: dict[str, Any]) -> Any:
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
        url = self.domain + endpoint
        async with ClientSession() as session:
            async with session.post(url=url, json=data, headers=headers, proxy=self.proxy, ssl=self.ssl) as resp:
                return await self.process_yango_response(resp, payload=data)


    @retry_request
    async def yango_multipart_request(self, endpoint: str, data: dict[str, Any]):
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
