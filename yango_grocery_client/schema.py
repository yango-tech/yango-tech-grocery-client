from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal
import io


"""
The class was added for clarity. Do not use it in other schemas.
Any random value can come from the API, this will break the transformation.

class YangoMarkCountUnitList(str, Enum):
    UNIT = 'unit'
    GRAM = 'gram'
    KG = 'kilogram'
    LITER = 'liter'
    MILLILITRE = 'millilitre'
    # truly can be anything
"""


class YangoOrderState(str, Enum):
    DRAFT = 'draft'
    CANCELED = 'canceled'
    CHECKED_OUT = 'checked_out'
    RESERVING = 'reserving'
    RESERVED = 'reserved'
    POSTPONE_RESERVING = 'postpone_reserving'
    POSTPONED = 'postponed'
    ASSEMBLING = 'assembling'
    ASSEMBLED = 'assembled'
    DELIVERING = 'delivering'
    CLOSED = 'closed'
    PENDING_CANCEL = 'pending_cancel'


class YangoOrderPickingState(str, Enum):
    RESERVING = 'reserving'
    APPROVING = 'approving'
    REQUEST = 'request'
    PROCESSING = 'processing'
    COMPLETE = 'complete'
    FAILED = 'failed'
    CANCELED = 'canceled'


class YangoOrderEventType(str, Enum):
    STATE_CHANGE = 'state_change'
    NEW_ORDER = 'new_order'
    RECEIPT_ISSUED = 'receipt_issued'


class YangoTypeAccounting(str, Enum):
    TRUE_WEIGHT = 'byTrueWeight'
    UNIT = 'byUnit'
    WEIGHT = 'byWeight'


class YangoNomenclatureType(str, Enum):
    PRODUCT = 'product'


class YangoProductStatus(str, Enum):
    ACTIVE = 'active'
    DISABLED = 'disabled'
    ARCHIVED = 'archived'


class YangoPriceListStatus(str, Enum):
    ACTIVE = 'active'
    REMOVED = 'removed'


class YangoMediaType(str, Enum):
    IMAGE = 'image'
    VIDEO = 'video'


class YangoMediaPosition(str, Enum):
    FIRST = 'first'
    LAST = 'last'


class YangoStockUpdateMode(str, Enum):
    INIT = 'initialize'
    MODIFY = 'modify'


AttributeTranslations = dict[str, str] # {lang_code: name}


@dataclass
class YangoShoppingCartItem:
    product_id: str
    quantity: int
    price: str
    discount: str | None = None
    vat: str | None = None


@dataclass
class YangoOrderCart:
    items: list[YangoShoppingCartItem]
    total_price: str
    total_delivery: str | None = None
    total_discount: str | None = None
    total_package: str | None = None
    total_promo: str | None = None
    total_vat: str | None = None


@dataclass
class Point:
    lat: float
    lon: float


@dataclass
class YangoAddress:
    city: str | None = None
    country: str | None = None
    house: str | None = None
    street: str | None = None


@dataclass
class YangoDeliveryAddress:
    position: Point
    address: YangoAddress | None = None
    comment: str | None = None


@dataclass
class YangoDeliverySlot:
    start: str
    end: str


@dataclass
class YangoDeliveryProperties:
    type: str
    slot: YangoDeliverySlot | None = None


@dataclass(kw_only=True)
class YangoOrderRecord:
    order_id: str
    cart: YangoOrderCart | None = None
    client_phone_number: str | None = None
    courier_pin: str | None = None
    delivery_address: YangoDeliveryAddress | None = None
    payment_type: str | None = None
    store_id: str | None = None
    use_external_logistics: bool | None = None
    delivery_properties: YangoDeliveryProperties | None = None


@dataclass(kw_only=True)
class YangoOrderDetails(YangoOrderRecord):
    create_time: str


@dataclass(kw_only=True)
class YangoStateChangeEventData:
    type: Literal[YangoOrderEventType.STATE_CHANGE]
    current_state: YangoOrderState


@dataclass(kw_only=True)
class YangoNewOrderEventData:
    type: Literal[YangoOrderEventType.NEW_ORDER]

@dataclass(kw_only=True)
class YangoReceiptIssuedEventData:
    type: Literal[YangoOrderEventType.RECEIPT_ISSUED]
    receipt_id: str


@dataclass(kw_only=True)
class YangoOrderEvent:
    data: YangoStateChangeEventData | YangoNewOrderEventData | YangoReceiptIssuedEventData
    order_id: str
    occurred: str

@dataclass(kw_only=True)
class YangoOrderEventQueryResponse:
    cursor: str
    orders_events: list[YangoOrderEvent]

@dataclass(kw_only=True)
class YangoReceiptOrder:
    id: str
    create_time: str | None = None


@dataclass(kw_only=True)
class YangoReceiptStore:
    id: str | None = None
    name: str | None = None
    address: str | None = None


@dataclass(kw_only=True)
class YangoReceiptItemVat:
    vat_amount: str
    vat_percent: str


@dataclass(kw_only=True)
class YangoReceiptPaymentAmount:
    payment_id: str
    price: str


@dataclass(kw_only=True)
class YangoReceiptItemPayment:
    quantity: str
    discount: str
    discount_amount: str = '0'
    payment_amounts: list[YangoReceiptPaymentAmount]
    barcode: str | None = None


@dataclass(kw_only=True)
class YangoReceiptProductItem:
    item_type: str
    name: AttributeTranslations
    payments: list[YangoReceiptItemPayment]
    vat: str | None = None


@dataclass(kw_only=True)
class YangoReceiptNotProductItem: # delivery, tips or service fee
    item_type: str
    title: AttributeTranslations | None = None
    payments: list[YangoReceiptItemPayment]
    vat: str | None = None


@dataclass(kw_only=True)
class YangoReceiptClientFullName:
    first_name: str | None = None
    last_name: str | None = None


@dataclass(kw_only=True)
class YangoReceiptClient:
    full_name: YangoReceiptClientFullName | None = None
    phone_number: str | None = None
    email: str | None = None
    delivery_address: YangoAddress | None = None


@dataclass(kw_only=True)
class YangoPaymentMethod:
    payment_type: str # cash, online, apple_pay, etc


class YangoReceiptType(str, Enum):
    PAYMENT = 'payment'
    REFUND = 'refund'


@dataclass(kw_only=True)
class YangoReceiptRecord:
    receipt_id: str
    order: YangoReceiptOrder
    create_time: str
    store: YangoReceiptStore
    receipt_type: YangoReceiptType | str
    payment_methods: dict[str, YangoPaymentMethod]
    items: dict[str, YangoReceiptProductItem | YangoReceiptNotProductItem]
    client: YangoReceiptClient | None = None


@dataclass(kw_only=True)
class YangoGetReceiptResponse:
    receipts: list[YangoReceiptRecord]


@dataclass
class YangoPriceListUpdateData:
    id: str
    name: str


@dataclass
class YangoPriceListData(YangoPriceListUpdateData):
    status: YangoPriceListStatus


@dataclass
class YangoPriceData:
    product_id: str
    price: float
    price_list_id: str
    price_per_quantity: int = 1


@dataclass
class YangoStorePriceLinkData:
    wms_store_id: str
    price_list_id: str


@dataclass
class YangoCustomAttributes:
    longName: dict[str, str]
    shortNameLoc: dict[str, str]
    markCount: float
    markCountUnitList: str # YangoMarkCountUnitList
    barcode: list[str] = field(default_factory=list[str])
    images: list[str] | None = None
    descriptionLoc: dict[str, str] | None = None
    nomenclatureType: YangoNomenclatureType | str | None = None
    typeAccounting: YangoTypeAccounting | str | None = None
    extraAttributes: dict[str, Any] | None = None


@dataclass
class YangoProductData:
    custom_attributes: YangoCustomAttributes
    master_category: str
    product_id: str
    status: YangoProductStatus | str
    is_meta: bool



@dataclass
class YangoStockData:
    product_id: str
    quantity: int


@dataclass
class YangoProductMedia:
    data: io.BytesIO
    product_id: str
    media_type: YangoMediaType
    position: YangoMediaPosition


@dataclass
class YangoDiscountRecord:
    product_id: str
    store_id: str
    discount_activity_period: dict[str, str]
    discount_value: dict[str, str]


@dataclass
class YangoProductVat:
    product_id: str
    vat: str


@dataclass(kw_only=True)
class YangoStoreRecord:
    id: str
    status: str
    location: Point
    address: str | None = None
    name: str | None = None
