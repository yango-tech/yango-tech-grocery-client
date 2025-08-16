"""
Yango Tech Grocery API Client

A Python client library for interacting with the Yango Tech Grocery API.
"""

__version__ = "0.1.0"
__author__ = "Yango Tech"
__email__ = "tech@yango.com"

from .client import YangoClient
from .base_client import BaseYangoClient
from .prices import YangoPricesClient
from .exceptions import YangoException, YangoRequestError, YangoBadRequest

# Import main schema classes for convenience
from .schema import (
    YangoOrderRecord,
    YangoShoppingCartItem,
    YangoProductData,
    YangoStoreRecord,
    YangoStockData,
    YangoPriceData,
    YangoOrderState,
    YangoProductStatus,
    YangoStockUpdateMode,
    YangoOrderEvent,
    YangoOrderEventType,
    YangoCustomAttributes,
    YangoProductMedia,
    YangoProductVat,
    YangoGetReceiptResponse,
    YangoOrderEventQueryResponse,
)

__all__ = [
    # Main client classes
    "YangoClient",
    "BaseYangoClient", 
    "YangoPricesClient",
    
    # Exceptions
    "YangoException",
    "YangoRequestError",
    "YangoBadRequest",
    
    # Schema classes
    "YangoOrderRecord",
    "YangoShoppingCartItem", 
    "YangoProductData",
    "YangoStoreRecord",
    "YangoStockData",
    "YangoPriceData",
    "YangoOrderState",
    "YangoProductStatus",
    "YangoStockUpdateMode",
    "YangoOrderEvent",
    "YangoOrderEventType",
    "YangoCustomAttributes",
    "YangoProductMedia",
    "YangoProductVat",
    "YangoGetReceiptResponse",
    "YangoOrderEventQueryResponse",
]
