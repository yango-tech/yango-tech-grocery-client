import logging
from collections.abc import AsyncGenerator
from dataclasses import asdict, fields
from enum import Enum
from typing import Any

from dacite import Config, from_dict

from .client_prices import YangoPricesClient
from .client_third_party_logistics import YangoThirdPartyLogisticsClient
from .constants import PRODUCTS_BATCH_SIZE, PRODUCTS_REQUEST_LIMIT, SERVICE_NAME, STOCKS_BATCH_SIZE, VAT_BATCH_SIZE
from .endpoints import (
    LOGISTIC_DELIVERY_SET_STATE_ENDPOINT,
    ORDER_CANCEL_ENDPOINT,
    ORDER_CREATE_ENDPOINT,
    ORDER_DETAIL_ENDPOINT,
    ORDER_UPDATE_ENDPOINT,
    ORDERS_EVENTS_QUERY_ENDPOINT,
    ORDERS_STATE_ENDPOINT,
    PRODUCT_CREATE_ENDPOINT,
    PRODUCT_MEDIA_CREATE_ENDPOINT,
    PRODUCT_UPDATES_ENDPOINT,
    PRODUCT_VAT_CREATE_ENDPOINT,
    PRODUCT_VAT_GET_ENDPOINT,
    PRODUCT_VAT_UPDATE_ENDPOINT,
    RECEIPTS_GET_ENDPOINT,
    RECEIPTS_UPLOAD_ENDPOINT,
    STOCK_GET_ENDPOINT,
    STOCK_INITIALIZE_ENDPOINT,
    STOCK_UPDATE_ENDPOINT,
    STORES_GET_ENDPOINT,
    WMS_PICKING_SET_STATE_ENDPOINT,
)
from .schema import (
    YangoCustomAttributes,
    YangoGetReceiptResponse,
    YangoNewOrderEventData,
    YangoOrderDetails,
    YangoOrderEvent,
    YangoOrderEventQueryResponse,
    YangoOrderEventType,
    YangoOrderRecord,
    YangoOrderState,
    YangoOrderStateQuery,
    YangoProductData,
    YangoProductMedia,
    YangoProductStatus,
    YangoProductVat,
    YangoReceiptClientField,
    YangoReceiptIssuedEventData,
    YangoStateChangeEventData,
    YangoStockData,
    YangoStockUpdateMode,
    YangoStoreRecord,
)

logger = logging.getLogger(SERVICE_NAME)


class YangoClient(YangoThirdPartyLogisticsClient, YangoPricesClient):
    async def create_order(self, data: YangoOrderRecord) -> Any:
        return await self.yango_request(ORDER_CREATE_ENDPOINT, asdict(data))

    async def cancel_order(self, order_id: str, reason: str | None = None) -> Any:
        data = {'order_id': order_id}

        if reason:
            data['reason'] = reason

        return await self.yango_request(ORDER_CANCEL_ENDPOINT, data)

    async def update_order(self, data: YangoOrderRecord) -> Any:
        return await self.yango_request(ORDER_UPDATE_ENDPOINT, asdict(data))

    async def get_order_detail(self, order_id: str) -> YangoOrderDetails:
        data = {'order_id': order_id}
        response = await self.yango_request(ORDER_DETAIL_ENDPOINT, data)

        return from_dict(YangoOrderDetails, {'order_id': order_id, **response})

    async def get_orders_state(self, order_ids: list[str]) -> list[YangoOrderStateQuery]:
        data = {'orders': order_ids}
        response = await self.yango_request(ORDERS_STATE_ENDPOINT, data)

        return [from_dict(YangoOrderStateQuery, orders_state) for orders_state in response['query_results']]

    def process_order_event_data(
        self, event: dict[str, Any]
    ) -> YangoStateChangeEventData | YangoNewOrderEventData | YangoReceiptIssuedEventData:
        if event['type'] == YangoOrderEventType.STATE_CHANGE:
            return YangoStateChangeEventData(type=event['type'], current_state=YangoOrderState(event['current_state']))
        if event['type'] == YangoOrderEventType.NEW_ORDER:
            return YangoNewOrderEventData(type=event['type'])
        if event['type'] == YangoOrderEventType.RECEIPT_ISSUED:
            return YangoReceiptIssuedEventData(type=event['type'], receipt_id=event['receipt_id'])
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
                    data=self.process_order_event_data(event['data']),
                )
                for event in response.get('orders_events', [])
            ],
        )

    async def get_receipt(
        self,
        *,
        receipt_id: str | None = None,
        order_id: str | None = None,
        client_fields: list[YangoReceiptClientField] | None = None,
    ) -> YangoGetReceiptResponse:
        data = {}

        if receipt_id and order_id:
            # according to Yango API
            raise Exception("Exactly one of the fields 'order_id', 'receipt_id' required")

        if receipt_id:
            data['receipt_id'] = receipt_id
        elif order_id:
            data['order_id'] = order_id
        else:
            raise Exception("One of the fields 'order_id' or 'receipt_id' is required")

        if client_fields:
            data['client_fields'] = client_fields

        response = await self.yango_request(RECEIPTS_GET_ENDPOINT, data)

        return from_dict(YangoGetReceiptResponse, response, config=Config(cast=[Enum]))

    async def upload_receipt(self, receipt_id: str, document: str) -> None:
        data = {'receipt_id': receipt_id, 'document': document, 'content_type': 'application/pdf'}
        await self.yango_request(RECEIPTS_UPLOAD_ENDPOINT, data)

    async def set_order_state_in_wms(self, order_id: str, state: str) -> None:
        data = {'order_id': order_id, 'state': state}
        await self.yango_request(WMS_PICKING_SET_STATE_ENDPOINT, data)

    async def set_order_state_in_logistic(self, order_id: str, state: str) -> None:
        data = {'order_id': order_id, 'state': state}
        await self.yango_request(LOGISTIC_DELIVERY_SET_STATE_ENDPOINT, data)

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
                product['custom_attributes'] = from_dict(
                    YangoCustomAttributes, base_attributes, config=Config(cast=[Enum])
                )
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
        created_product_count = 0
        for products_slice in self.batch_items(products, PRODUCTS_BATCH_SIZE):
            data = {'products': [asdict(pd) for pd in products_slice]}
            await self.yango_request(PRODUCT_CREATE_ENDPOINT, data)

            created_product_count += len(products_slice)
            logger.info(f'Create {created_product_count}/{len(products)} products')

        logger.info(f'{created_product_count} products are created')

    async def create_product_media(self, media: YangoProductMedia) -> None:
        request_data = asdict(media)
        await self.yango_multipart_request(PRODUCT_MEDIA_CREATE_ENDPOINT, data=request_data)

    async def update_stocks(self, wms_store_id: str, stocks: list[YangoStockData]) -> None:
        updated_stocks_count = 0
        for stocks_slice in self.batch_items(stocks, STOCKS_BATCH_SIZE):
            data: dict[str, Any] = {
                'update_mode': YangoStockUpdateMode.MODIFY,
                'store_id': wms_store_id,
                'stocks': [asdict(stock) for stock in stocks_slice],
            }
            await self.yango_request(STOCK_UPDATE_ENDPOINT, data)

            updated_stocks_count += len(stocks_slice)
            logger.info(f'Update {updated_stocks_count}/{len(stocks)} stocks')

        logger.info(f'{updated_stocks_count} stocks are updated')

    async def initialize_stocks(self, wms_store_id: str, stocks: list[YangoStockData]) -> None:
        data: dict[str, Any] = {'store_id': wms_store_id, 'stocks': [asdict(stock) for stock in stocks]}
        await self.yango_request(STOCK_INITIALIZE_ENDPOINT, data)

    async def get_stocks(self, cursor: str | None = None) -> dict[str, Any]:
        data: dict[str, Any] = {}

        if cursor is not None:
            data['cursor'] = cursor

        return await self.yango_request(STOCK_GET_ENDPOINT, data)

    async def get_product_vats(self, product_ids: list[str]) -> list[dict[str, Any]]:
        data = {'product_ids': product_ids}
        response = await self.yango_request(PRODUCT_VAT_GET_ENDPOINT, data)
        return response['results']

    async def update_product_vat(self, product_vats: list[YangoProductVat]) -> None:
        updated_product_vat_count = 0
        for product_vats_slice in self.batch_items(product_vats, VAT_BATCH_SIZE):
            data = {'products_vat': [asdict(vat) for vat in product_vats_slice]}
            await self.yango_request(PRODUCT_VAT_UPDATE_ENDPOINT, data)

            updated_product_vat_count += len(product_vats_slice)
            logger.info(f'Update {updated_product_vat_count}/{len(product_vats)} product VATs')

        logger.info(f'{updated_product_vat_count} product VATs are updated')

    async def create_product_vat(self, product_vats: list[YangoProductVat]) -> None:
        created_product_vat_count = 0
        for product_vats_slice in self.batch_items(product_vats, VAT_BATCH_SIZE):
            data = {'products_vat': [asdict(vat) for vat in product_vats_slice]}
            await self.yango_request(PRODUCT_VAT_CREATE_ENDPOINT, data)

            created_product_vat_count += len(product_vats_slice)
            logger.info(f'Create {created_product_vat_count}/{len(product_vats)} product VATs')

        logger.info(f'{created_product_vat_count} product VATs are created')

    async def get_stores(self) -> list[YangoStoreRecord]:
        response = await self.yango_request(STORES_GET_ENDPOINT, {})

        return [from_dict(YangoStoreRecord, store) for store in response['stores']]
