import asyncio
from dacite import from_dict
from dataclasses import asdict, fields
from enum import Enum
from functools import wraps
import json
from typing import Any, AsyncGenerator, Awaitable, Callable, ParamSpec, TypeVar

import aiohttp

from logger.logger import get_logger
from aiohttp import ClientSession
from .endpoints import (
    DISCOUNTS_CREATE_ENDPOINT, LOGISTIC_DELIVERY_SET_STATE_ENDPOINT, ORDER_CANCEL_ENDPOINT,
    ORDER_CREATE_ENDPOINT, ORDER_DETAIL_ENDPOINT, ORDER_UPDATE_ENDPOINT, ORDERS_EVENTS_QUERY_ENDPOINT,
    ORDERS_STATE_ENDPOINT,
    PRICE_CREATE_ENDPOINT, PRICE_GET_ENDPOINT, PRICE_LIST_CREATE_ENDPOINT, PRICE_SET_ENDPOINT,
    PRICE_UPDATE_ENDPOINT,
    PRODUCT_CREATE_ENDPOINT, PRODUCT_UPDATES_ENDPOINT,
    PRODUCT_MEDIA_CREATE_ENDPOINT,
    PRODUCT_VAT_CREATE_ENDPOINT, PRODUCT_VAT_UPDATE_ENDPOINT, PRODUCT_VAT_GET_ENDPOINT,
    RECEIPTS_GET_ENDPOINT, RECEIPTS_UPLOAD_ENDPOINT,
    STOCK_GET_ENDPOINT, STOCK_UPDATE_ENDPOINT,
    STORE_PRICE_LIST_LINK_CREATE_ENDPOINT, STORE_PRICE_LIST_LINK_GET_ENDPOINT,
    STORES_GET_ENDPOINT, WMS_PICKING_SET_STATE_ENDPOINT,
    PRICE_LIST_UPDATES_ENDPOINT, PRICE_LIST_GET_ENDPOINT
)
from .constants import (
    DEFAULT_REQUEST_LIMIT, DISCOUNTS_BATCH_SIZE, ERROR_STATUSES_FOR_RETRY, MAX_RETRIES, PRODUCTS_REQUEST_LIMIT, SERVICE_NAME
)
from .exceptions import YangoBadRequest, YangoRequestError
from .schema import (
    YangoGetReceiptResponse, YangoOrderRecord, YangoStoreRecord, YangoProductData, YangoPriceListData,
    YangoProductMedia, YangoPriceData, YangoStorePriceLinkData, YangoDiscountRecord, YangoStockData,
    YangoStockUpdateMode, YangoProductVat, YangoProductStatus, YangoCustomAttributes, YangoOrderEventQueryResponse,
    YangoStateChangeEventData, YangoNewOrderEventData, YangoReceiptIssuedEventData, YangoOrderState, YangoOrderEvent,
    YangoOrderEventType
)


logger = get_logger(SERVICE_NAME)


P = ParamSpec('P')
R = TypeVar('R')


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
                    await asyncio.sleep(1)
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


class YangoClient:

    def __init__(
        self, domain: str, auth_token: str,
        error_handler: YangoErrorHandler | None = None
    ):
        self.auth_token = auth_token
        self.domain = domain
        self.error_handler = error_handler


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
    async def yango_request(self, endpoint: str, data: dict[str, Any]):
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
        url = self.domain + endpoint
        async with ClientSession() as session:
            async with session.post(url=url, json=data, headers=headers) as resp:
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
            async with session.post(url=url, data=form_data, headers=headers) as resp:
                return await self.process_yango_response(resp)


    async def create_order(self, data: YangoOrderRecord):
        return await self.yango_request(ORDER_CREATE_ENDPOINT, asdict(data))


    async def cancel_order(self, order_id: str, reason: str | None = None):
        data = {'order_id': order_id}

        if reason:
            data['reason'] = reason

        return await self.yango_request(ORDER_CANCEL_ENDPOINT, data)


    async def update_order(self, data: YangoOrderRecord):
        return await self.yango_request(ORDER_UPDATE_ENDPOINT, asdict(data))


    async def get_order_detail(self, order_id: str):
        data = {'order_id': order_id}
        return await self.yango_request(ORDER_DETAIL_ENDPOINT, data)


    async def get_orders_state(self, order_ids: list[str]):
        data = {'orders': order_ids}
        return await self.yango_request(ORDERS_STATE_ENDPOINT, data)

    def process_order_event_data(self, event: dict[str, Any]) -> YangoStateChangeEventData | YangoNewOrderEventData | YangoReceiptIssuedEventData:
        if event['type'] == YangoOrderEventType.STATE_CHANGE:
            return YangoStateChangeEventData(
                type=event['type'],
                current_state=YangoOrderState(event['current_state'])
            )
        if event['type'] == YangoOrderEventType.NEW_ORDER:
            return YangoNewOrderEventData(
                type=event['type']
            )
        if event['type'] == YangoOrderEventType.RECEIPT_ISSUED:
            return YangoReceiptIssuedEventData(
                type=event['type'],
                receipt_id=event['receipt_id']
            )
        raise ValueError(f'Unknown event type {event["type"]}')

    async def get_orders_events_query(self, cursor: str | None = None) -> YangoOrderEventQueryResponse:
        data: dict[str, Any] = {}

        if cursor is not None:
            data['cursor'] = cursor

        response = await self.yango_request(ORDERS_EVENTS_QUERY_ENDPOINT, data)
        return YangoOrderEventQueryResponse(
            cursor=response['cursor'],
            orders_events=[
                YangoOrderEvent(
                    order_id=event['order_id'],
                    occurred=event['occurred'],
                    data=self.process_order_event_data(event['data'])
                ) for event in response.get('orders_events', [])
            ]
        )


    async def get_receipt(self, receipt_id: str) -> YangoGetReceiptResponse:
        data = {'receipt_id': receipt_id}

        response = await self.yango_request(RECEIPTS_GET_ENDPOINT, data)

        return from_dict(YangoGetReceiptResponse, response)


    async def upload_receipt(self, receipt_id: str, document: str):
        data = {
            'receipt_id': receipt_id,
            'document': document,
            'content_type': 'application/pdf'
        }
        return await self.yango_request(RECEIPTS_UPLOAD_ENDPOINT, data)


    async def set_order_state_in_wms(self, order_id: str, state: str):
        data = {'order_id': order_id, 'state': state}
        return await self.yango_request(WMS_PICKING_SET_STATE_ENDPOINT, data)


    async def set_order_state_in_logistic(self, order_id: str, state: str):
        data = {'order_id': order_id, 'state': state}
        return await self.yango_request(LOGISTIC_DELIVERY_SET_STATE_ENDPOINT, data)


    def filter_extra_attributes(self, attribute_dict: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        """
            Filter extra attributes from the product data
            Extra attributes are those that are not in the CustomAttributes schema
        """
        extra_attributes: dict[str, Any] = {}
        custom_attributes: dict[str, Any] = {}

        base_fields = {field.name for field in fields(YangoCustomAttributes)}
        for key, value in attribute_dict.items():
            if key in base_fields:
                custom_attributes[key] = value
            else:
                extra_attributes[key] = value

        return custom_attributes, extra_attributes


    async def get_product_updates(self, cursor: str | None = None) -> AsyncGenerator[YangoProductData, None]:
        """
            Returns an async generator that yields product update from WMS, starting from the cursor
            If you want full snapshot - use get_all_products
        """
        logger.info('Loading existing products from WMS')
        total_product_count = 0
        while True:
            data: dict[str, Any] = {'cursor': cursor, 'limit': PRODUCTS_REQUEST_LIMIT}
            response = await self.yango_request(PRODUCT_UPDATES_ENDPOINT, data)
            products = response['products']
            cursor = response['cursor']
            total_product_count += len(products)
            logger.info(f'Loaded {total_product_count} products from WMS')
            for product in products:
                base_attributes, extra_attributes = self.filter_extra_attributes(product['custom_attributes'])
                custom_attributes = YangoCustomAttributes(
                    extraAttributes=extra_attributes,
                    **base_attributes
                )
                del product['custom_attributes']
                yield YangoProductData(
                    custom_attributes=custom_attributes,
                    **product
                )
            if len(products) < PRODUCTS_REQUEST_LIMIT:
                return

    async def get_all_products(self, only_active: bool = True) -> dict[str, YangoProductData]:
        """
            Returns all products from WMS as a dict with product_id as a key
        """
        products: dict[str, YangoProductData] = {}
        async for product in self.get_product_updates():
            if only_active and product.status != YangoProductStatus.ACTIVE:
                if product.product_id in products:
                    del products[product.product_id]
                continue
            products[product.product_id] = product
        return products


    async def create_products(self, products: list[YangoProductData]) -> None:
        data = {
            'products': [asdict(pd) for pd in products]
        }
        await self.yango_request(PRODUCT_CREATE_ENDPOINT, data)


    async def create_product_media(self, media: YangoProductMedia) -> None:
        request_data = asdict(media)
        await self.yango_multipart_request(PRODUCT_MEDIA_CREATE_ENDPOINT, data=request_data)

    async def create_price_lists(self, price_lists: list[YangoPriceListData]) -> None:
        data = {
            'pricelists': [asdict(pl) for pl in price_lists]
        }
        await self.yango_request(PRICE_LIST_CREATE_ENDPOINT, data)


    async def get_price_lists(self, price_list_ids: list[str]):
        data = {
            'pricelist_ids': price_list_ids
        }
        result = await self.yango_request(PRICE_LIST_GET_ENDPOINT, data)
        return result['results']

    async def get_price_list_updates(self, cursor: str | None = None) -> AsyncGenerator[YangoPriceListData, None]:
        logger.info('Loading existing products from WMS')
        while True:
            data: dict[str, Any] = {'cursor': cursor, 'limit': DEFAULT_REQUEST_LIMIT}
            response = await self.yango_request(PRICE_LIST_UPDATES_ENDPOINT, data)
            price_lists = response['pricelists']
            cursor = response['cursor']
            for price_list in price_lists:
                yield YangoPriceListData(**price_list)
            if len(price_lists) < DEFAULT_REQUEST_LIMIT:
                return

    async def get_all_price_lists(self) -> dict[str, YangoPriceListData]:
        """
            Returns all price lists from WMS as a dict with price_list_id as a key
        """
        price_lists: dict[str, YangoPriceListData] = {}
        async for price_list in self.get_price_list_updates():
            price_lists[price_list.id] = price_list
        return price_lists

    async def get_store_price_list_links(self, wms_store_ids: list[str]):
        data = {
            'store_ids': wms_store_ids
        }
        result = await self.yango_request(STORE_PRICE_LIST_LINK_GET_ENDPOINT, data)
        return result['results']


    async def create_store_price_list_links(self, links: list[YangoStorePriceLinkData]) -> None:
        link_data: list[dict[str, Any]] = []
        for link in links:
            link_data.append(
                {'store_id': link.wms_store_id, 'pricelist_id': link.price_list_id}
            )
        data = {'links': link_data}
        await self.yango_request(STORE_PRICE_LIST_LINK_CREATE_ENDPOINT, data)


    async def get_prices(self, price_list_ids: list[str]) -> dict[str, list[YangoPriceData]]:
        data = {
            'pricelist_ids': price_list_ids
        }
        response = await self.yango_request(PRICE_GET_ENDPOINT, data)
        pricelists = response['results']
        result: dict[str, list[YangoPriceData]] = {}
        for pricelist in pricelists:
            list_id = pricelist['pricelist_id']
            prices: list[YangoPriceData] = []
            for price_data in pricelist['prices_data']:
                prices.append(YangoPriceData(
                    product_id=price_data['product_id'],
                    price=price_data['price'],
                    price_list_id=list_id
                ))
            result[list_id] = prices
        return result


    def get_price_request_data(self, price_record: YangoPriceData) -> dict[str, Any]:
        return {
            'price': str(price_record.price), 'pricelist_id': price_record.price_list_id,
            'product_id': price_record.product_id, 'price_per_quantity': price_record.price_per_quantity
        }

    async def update_prices(self, prices: list[YangoPriceData]):
        prices_data = [self.get_price_request_data(price) for price in prices]
        data = {'prices': prices_data}
        return await self.yango_request(PRICE_UPDATE_ENDPOINT, data)

    async def set_prices(self, prices: list[YangoPriceData]):
        prices_data = [self.get_price_request_data(price) for price in prices]
        data = {'prices': prices_data}
        return await self.yango_request(PRICE_SET_ENDPOINT, data)


    async def get_prices_dict(self, price_list_ids: list[str]) -> dict[str, dict[str, YangoPriceData]]:
        price_lists = await self.get_prices(price_list_ids)
        result: dict[str, dict[str, YangoPriceData]] = {}
        for pricelist_id, prices in price_lists.items():
            price_dict = {}
            for price in prices:
                price_dict[price.product_id] = price
            result[pricelist_id] = price_dict
        return result


    async def create_prices(self, prices: list[YangoPriceData]):
        prices_data = [self.get_price_request_data(price) for price in prices]
        data = {'prices': prices_data}
        return await self.yango_request(PRICE_CREATE_ENDPOINT, data)


    async def create_discounts(self, discounts: list[YangoDiscountRecord]):
        if not discounts:
            logger.info('No discounts for creating')
            return

        slice_start = 0

        while slice_start < len(discounts):
            discounts_slice = discounts[slice_start:slice_start+DISCOUNTS_BATCH_SIZE]

            data = {'discounts': [asdict(d) for d in discounts_slice]}
            response = await self.yango_request(DISCOUNTS_CREATE_ENDPOINT, data)

            logger.info(f'Create {len(discounts_slice)} discounts: {response}')

            slice_start += DISCOUNTS_BATCH_SIZE


    async def update_stocks(self, wms_store_id: str, stocks: list[YangoStockData]):
        data: dict[str, Any] = {
            'update_mode': YangoStockUpdateMode.MODIFY,
            'store_id': wms_store_id,
            'stocks': [asdict(stock) for stock in stocks]
        }
        return await self.yango_request(STOCK_UPDATE_ENDPOINT, data)

    async def get_stocks(self, cursor: str | None = None):
        data: dict[str, Any] = {}

        if cursor is not None:
            data['cursor'] = cursor

        return await self.yango_request(STOCK_GET_ENDPOINT, data)

    async def get_product_vat(self, product_ids: list[str]):
        data = {
            'product_ids': product_ids
        }
        return await self.yango_request(PRODUCT_VAT_GET_ENDPOINT, data)

    async def update_product_vat(self, product_vat_data: list[YangoProductVat]):
        data = {
            'products_vat': [asdict(vat) for vat in product_vat_data]
        }
        return await self.yango_request(PRODUCT_VAT_UPDATE_ENDPOINT, data)

    async def create_product_vat(self, product_vat_data: list[YangoProductVat]):
        data = {
            'products_vat': [asdict(vat) for vat in product_vat_data]
        }
        return await self.yango_request(PRODUCT_VAT_CREATE_ENDPOINT, data)

    async def get_stores(self) -> list[YangoStoreRecord]:
        response = await self.yango_request(STORES_GET_ENDPOINT, {})

        return [from_dict(YangoStoreRecord, store) for store in response['stores']]
