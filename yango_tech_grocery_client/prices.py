import logging
from collections.abc import AsyncGenerator
from dataclasses import asdict
from typing import Any

from dacite import from_dict

from .base_client import BaseYangoClient
from .constants import DEFAULT_REQUEST_LIMIT, DISCOUNTS_BATCH_SIZE, PRICES_BATCH_SIZE, SERVICE_NAME
from .endpoints import (
    DISCOUNTS_CREATE_ENDPOINT,
    PRICE_GET_ENDPOINT,
    PRICE_LIST_CREATE_ENDPOINT,
    PRICE_LIST_GET_ENDPOINT,
    PRICE_LIST_UPDATES_ENDPOINT,
    PRICE_SET_ENDPOINT,
    STORE_PRICE_LIST_LINK_CREATE_ENDPOINT,
    STORE_PRICE_LIST_LINK_GET_ENDPOINT,
)
from .schema import (
    YangoDiscountRecord,
    YangoPriceData,
    YangoPriceListData,
    YangoPriceListUpdateData,
    YangoStorePriceLinkData,
)

logger = logging.getLogger(SERVICE_NAME)


def get_price_request_data(price_record: YangoPriceData) -> dict[str, Any]:
    return {
        'price': str(price_record.price),
        'pricelist_id': price_record.price_list_id,
        'product_id': price_record.product_id,
        'price_per_quantity': price_record.price_per_quantity,
    }


class YangoPricesClient(BaseYangoClient):
    """
    Client module for working with Yango prices and price lists.
    Inherits from BaseYangoClient to handle common request logic.
    Shouldn't be used directly, use YangoClient instead.
    """

    async def create_price_lists(self, price_lists: list[YangoPriceListUpdateData]) -> None:
        data = {'pricelists': [asdict(pl) for pl in price_lists]}
        await self.yango_request(PRICE_LIST_CREATE_ENDPOINT, data)

    async def get_price_lists(self, price_list_ids: list[str]) -> list[dict[str, Any]]:
        data = {'pricelist_ids': price_list_ids}
        result = await self.yango_request(PRICE_LIST_GET_ENDPOINT, data)
        return result['results']

    async def sync_price_lists(self, price_list_ids: set[str]) -> None:
        logger.info(f'{len(price_list_ids)} price lists found')

        existing_price_lists = await self.get_price_lists(list(price_list_ids))
        logger.info(f'{len(existing_price_lists)} price lists already exist in WMS')

        lists_to_create = [
            YangoPriceListUpdateData(pl['pricelist_id'], pl['pricelist_id'])
            for pl in existing_price_lists
            if pl['get_result'] == 'pricelist_not_found'
        ]
        logger.info(f'{len(lists_to_create)} price lists need to be created')

        if len(lists_to_create) > 0:
            await self.create_price_lists(lists_to_create)

    async def get_price_list_updates(self, cursor: str | None = None) -> AsyncGenerator[YangoPriceListData, None]:
        logger.info('Loading existing products from WMS')
        while True:
            data: dict[str, Any] = {'cursor': cursor, 'limit': DEFAULT_REQUEST_LIMIT}
            response = await self.yango_request(PRICE_LIST_UPDATES_ENDPOINT, data)
            price_lists = response['pricelists']
            cursor = response['cursor']
            for price_list in price_lists:
                yield from_dict(YangoPriceListData, price_list)
            if len(price_lists) < DEFAULT_REQUEST_LIMIT:
                return

    async def get_all_price_lists(self) -> dict[str, YangoPriceListData]:
        """
        Get all price lists from Yango. Currently API only supports getting updates,
        so we need to iterate through all updates to collect all price lists.
        """

        price_lists: dict[str, YangoPriceListData] = {}
        async for price_list in self.get_price_list_updates():
            price_lists[price_list.id] = price_list
        return price_lists

    async def get_store_price_list_links(self, wms_store_ids: list[str]) -> Any:
        data = {'store_ids': wms_store_ids}
        result = await self.yango_request(STORE_PRICE_LIST_LINK_GET_ENDPOINT, data)
        return result['results']

    async def create_store_price_list_links(self, links: list[YangoStorePriceLinkData]) -> None:
        link_data: list[dict[str, Any]] = []
        for link in links:
            link_data.append({'store_id': link.wms_store_id, 'pricelist_id': link.price_list_id})
        data = {'links': link_data}
        await self.yango_request(STORE_PRICE_LIST_LINK_CREATE_ENDPOINT, data)

    async def sync_price_list_links(self, wms_store_id_to_price_list_id: dict[str, str]) -> None:
        wms_store_ids = set(wms_store_id_to_price_list_id.keys())
        existing_links = await self.get_store_price_list_links(list(wms_store_ids))
        logger.info(f'{len(existing_links)} price lists links already exist in WMS')

        wms_store_ids_to_create_links = [
            link['store_id'] for link in existing_links if not link.get('store_pricelist_link_data')
        ]
        logger.info(f'{len(wms_store_ids_to_create_links)} price lists links need to be created')

        for wms_store_id in wms_store_ids_to_create_links:
            price_list_id = wms_store_id_to_price_list_id[wms_store_id]

            await self.create_store_price_list_links(
                [YangoStorePriceLinkData(wms_store_id, price_list_id=price_list_id)]
            )

    async def get_prices(self, price_list_ids: list[str]) -> dict[str, list[YangoPriceData]]:
        data = {'pricelist_ids': price_list_ids}
        response = await self.yango_request(PRICE_GET_ENDPOINT, data)
        pricelists = response['results']
        result: dict[str, list[YangoPriceData]] = {}
        for pricelist in pricelists:
            list_id = pricelist['pricelist_id']
            prices: list[YangoPriceData] = []
            for price_data in pricelist['prices_data']:
                prices.append(
                    YangoPriceData(
                        product_id=price_data['product_id'],
                        price=price_data['price'],
                        price_list_id=list_id,
                        price_per_quantity=price_data.get('price_per_quantity'),
                    )
                )
            result[list_id] = prices
        return result

    async def set_prices(self, prices: list[YangoPriceData]) -> None:
        set_price_count = 0
        for prices_slice in self.batch_items(prices, PRICES_BATCH_SIZE):
            data = {'prices': [get_price_request_data(price) for price in prices_slice]}
            await self.yango_request(PRICE_SET_ENDPOINT, data)

            set_price_count += len(prices_slice)
            logger.info(f'Set {set_price_count}/{len(prices)} prices')

        logger.info(f'{set_price_count} prices are set')

    async def get_prices_dict(self, price_list_ids: list[str]) -> dict[str, dict[str, YangoPriceData]]:
        price_lists = await self.get_prices(price_list_ids)
        result: dict[str, dict[str, YangoPriceData]] = {}
        for pricelist_id, prices in price_lists.items():
            price_dict = {}
            for price in prices:
                price_dict[price.product_id] = price
            result[pricelist_id] = price_dict
        return result

    async def create_discounts(self, discounts: list[YangoDiscountRecord]) -> None:
        created_discount_count = 0
        for discounts_slice in self.batch_items(discounts, DISCOUNTS_BATCH_SIZE):
            data = {'discounts': [asdict(d) for d in discounts_slice]}
            await self.yango_request(DISCOUNTS_CREATE_ENDPOINT, data)

            created_discount_count += len(discounts_slice)
            logger.info(f'Create {created_discount_count}/{len(discounts)} discounts')

        logger.info(f'{created_discount_count} discounts are created')
