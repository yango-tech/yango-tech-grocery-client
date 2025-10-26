"""
Yango Tech Grocery API Client

A Python client library for interacting with the Yango Tech Grocery API.
"""

__version__ = '1.0.0'
__author__ = 'Yango Tech'
__email__ = 'tech@yango.com'

from .base_client import BaseYangoClient
from .client import YangoClient
from .client_prices import YangoPricesClient
from .client_third_party_logistics import YangoThirdPartyLogisticsClient
from .exceptions import YangoException, YangoRequestError

# Import main schema classes for convenience
from .schema import (
    YangoCustomAttributes,
    YangoGetReceiptResponse,
    YangoOrderEvent,
    YangoOrderEventQueryResponse,
    YangoOrderEventType,
    YangoOrderRecord,
    YangoOrderState,
    YangoOrderStateQuery,
    YangoPriceData,
    YangoProductData,
    YangoProductMedia,
    YangoProductStatus,
    YangoProductVat,
    YangoShoppingCartItem,
    YangoStockData,
    YangoStockUpdateMode,
    YangoStoreRecord,
    YangoThirdPartyLogisticsDeliveryType,
)

__all__ = [
    # Main client classes
    'YangoClient',
    'BaseYangoClient',
    'YangoPricesClient',
    'YangoThirdPartyLogisticsClient',
    # Exceptions
    'YangoException',
    'YangoRequestError',
    # Schema classes
    'YangoOrderRecord',
    'YangoShoppingCartItem',
    'YangoProductData',
    'YangoStoreRecord',
    'YangoStockData',
    'YangoPriceData',
    'YangoOrderState',
    'YangoOrderStateQuery',
    'YangoProductStatus',
    'YangoStockUpdateMode',
    'YangoOrderEvent',
    'YangoOrderEventType',
    'YangoCustomAttributes',
    'YangoProductMedia',
    'YangoProductVat',
    'YangoGetReceiptResponse',
    'YangoOrderEventQueryResponse',
    'YangoThirdPartyLogisticsDeliveryType',
]
