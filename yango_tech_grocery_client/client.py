from dacite import Config, from_dict
from dataclasses import asdict, fields
from enum import Enum
from typing import Any, AsyncGenerator


from logger.logger import get_logger
from .endpoints import (
    LOGISTIC_DELIVERY_SET_STATE_ENDPOINT, ORDER_CANCEL_ENDPOINT,
    ORDER_CREATE_ENDPOINT, ORDER_DETAIL_ENDPOINT, ORDER_UPDATE_ENDPOINT, ORDERS_EVENTS_QUERY_ENDPOINT,
    ORDERS_STATE_ENDPOINT, PRODUCT_CREATE_ENDPOINT, PRODUCT_UPDATES_ENDPOINT,
    PRODUCT_MEDIA_CREATE_ENDPOINT,
    PRODUCT_VAT_CREATE_ENDPOINT, PRODUCT_VAT_UPDATE_ENDPOINT, PRODUCT_VAT_GET_ENDPOINT,
    RECEIPTS_GET_ENDPOINT, RECEIPTS_UPLOAD_ENDPOINT,
    STOCK_GET_ENDPOINT, STOCK_UPDATE_ENDPOINT,
    STORES_GET_ENDPOINT, WMS_PICKING_SET_STATE_ENDPOINT,
)
from .constants import PRODUCTS_REQUEST_LIMIT, SERVICE_NAME
from .schema import (
    YangoGetReceiptResponse, YangoOrderRecord, YangoStoreRecord, YangoProductData,
    YangoProductMedia, YangoStockData, YangoStockUpdateMode, YangoProductVat,
    YangoProductStatus, YangoCustomAttributes, YangoOrderEventQueryResponse,
    YangoStateChangeEventData, YangoNewOrderEventData, YangoReceiptIssuedEventData, YangoOrderState, YangoOrderEvent,
    YangoOrderEventType
)
from .prices import YangoPricesClient


logger = get_logger(SERVICE_NAME)



class YangoClient(YangoPricesClient):

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

        return from_dict(YangoGetReceiptResponse, response, config=Config(cast=[Enum]))


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
                base_attributes['extraAttributes'] = extra_attributes
                product['custom_attributes'] = from_dict(YangoCustomAttributes, base_attributes, config=Config(cast=[Enum]))
                yield from_dict(YangoProductData, product, config=Config(cast=[Enum]))
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
