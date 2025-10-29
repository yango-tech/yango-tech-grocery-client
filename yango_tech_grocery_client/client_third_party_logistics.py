import logging
from dataclasses import asdict

from dacite import from_dict

from .base_client import BaseYangoClient
from .constants import SERVICE_NAME
from .endpoints import (
    THIRD_PARTY_LOGISTICS_DELIVERIES_EVENTS_QUERY_ENDPOINT,
    THIRD_PARTY_LOGISTICS_DELIVERY_COURIER_INFO_UPDATE_ENDPOINT,
    THIRD_PARTY_LOGISTICS_DELIVERY_COURIER_POSITION_UPDATE_ENDPOINT,
    THIRD_PARTY_LOGISTICS_DELIVERY_STATUS_UPDATE_ENDPOINT,
)
from .schema import (
    YangoThirdPartyLogisticsDeliveryCourierInfo,
    YangoThirdPartyLogisticsDeliveryCourierPosition,
    YangoThirdPartyLogisticsDeliveryEvents,
    YangoThirdPartyLogisticsDeliveryStatus,
)

logger = logging.getLogger(SERVICE_NAME)


class YangoThirdPartyLogisticsClient(BaseYangoClient):
    """
    Client module for working with Yango Third-party Logistics
    Inherits from BaseYangoClient to handle common request logic.
    Shouldn't be used directly, use YangoClient instead.
    """

    async def get_deliveries_events(
        self, cursor: str | None = None, limit: int | None = None
    ) -> YangoThirdPartyLogisticsDeliveryEvents:
        data = {'cursor': cursor, 'limit': limit}
        response = await self.yango_request(THIRD_PARTY_LOGISTICS_DELIVERIES_EVENTS_QUERY_ENDPOINT, data)

        return from_dict(YangoThirdPartyLogisticsDeliveryEvents, response)

    async def update_delivery_status(self, delivery_id: int, status: YangoThirdPartyLogisticsDeliveryStatus) -> None:
        data = {'delivery_id': delivery_id, 'status': status}
        await self.yango_request(THIRD_PARTY_LOGISTICS_DELIVERY_STATUS_UPDATE_ENDPOINT, data)

    async def update_delivery_courier_info(
        self, delivery_id: int, courier_info: YangoThirdPartyLogisticsDeliveryCourierInfo
    ) -> None:
        data = {'delivery_id': delivery_id, 'courier': asdict(courier_info)}
        await self.yango_request(THIRD_PARTY_LOGISTICS_DELIVERY_COURIER_INFO_UPDATE_ENDPOINT, data)

    async def update_delivery_courier_position(
        self, delivery_id: int, courier_position: YangoThirdPartyLogisticsDeliveryCourierPosition
    ) -> None:
        data = {'delivery_id': delivery_id, 'courier_position': asdict(courier_position)}
        await self.yango_request(THIRD_PARTY_LOGISTICS_DELIVERY_COURIER_POSITION_UPDATE_ENDPOINT, data)
