import io
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

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
    COURIER_ASSIGNED = 'courier_assigned'


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


AttributeTranslations = dict[str, str]  # {lang_code: name}


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
    human_order_id: str | None = None


@dataclass(kw_only=True)
class YangoOrderDetails(YangoOrderRecord):
    create_time: str


@dataclass(kw_only=True)
class YangoOrderStateQuery(YangoOrderRecord):
    order_id: str
    query_result: str
    state: YangoOrderState | None = None


@dataclass(kw_only=True)
class YangoStateChangeEventData:
    type: Literal[YangoOrderEventType.STATE_CHANGE]
    current_state: YangoOrderState | str


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
class YangoReceiptNotProductItem:  # delivery, tips or service fee
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
    payment_type: str  # cash, online, apple_pay, etc


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


class YangoReceiptClientField(str, Enum):
    FULL_NAME = 'full_name'
    PHONE_NUMBER = 'phone_number'
    EMAIL = 'email'
    DELIVERY_ADDRESS = 'delivery_address'


@dataclass(kw_only=True)
class YangoGetReceiptResponse:
    receipts: list[YangoReceiptRecord]


@dataclass
class YangoPriceListUpdateData:
    id: str
    name: str


@dataclass
class YangoPriceListData(YangoPriceListUpdateData):
    status: YangoPriceListStatus | str


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
    markCountUnitList: str  # YangoMarkCountUnitList
    barcode: list[str] = field(default_factory=list[str])
    images: list[str] | None = None
    descriptionLoc: dict[str, str] | None = None
    nomenclatureType: YangoNomenclatureType | str | None = None
    typeAccounting: YangoTypeAccounting | str | None = None
    trueMark: bool | None = None
    mercury: bool | None = None
    oblastHran: str | None = None
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
    media_type: YangoMediaType | str
    position: YangoMediaPosition | str


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


@dataclass(kw_only=True)
class YangoStoreLocation:
    position: Point
    address: str | None = None


### 3pl


@dataclass(kw_only=True)
class YangoThirdPartyLogisticsDeliveryItem:
    price: str
    product_id: str
    title: str
    depth: int | None = None
    height: int | None = None
    quantity: str | None = None
    weight: int | None = None
    width: int | None = None


@dataclass(kw_only=True)
class YangoThirdPartyLogisticsDeliveryLocation:
    position: Point
    building_name: str | None = None
    city: str | None = None
    comment: str | None = None
    country: str | None = None
    doorbell_name: str | None = None
    doorcode: str | None = None
    doorcode_extra: str | None = None
    entrance: str | None = None
    flat: str | None = None
    floor: str | None = None
    house: str | None = None
    postal_code: str | None = None
    street: str | None = None


class YangoThirdPartyLogisticsDeliveryType(str, Enum):
    CREATE = 'create'
    CANCEL = 'cancel'


@dataclass(kw_only=True)
class YangoThirdPartyLogisticsDeliveryCreated:
    type: Literal[YangoThirdPartyLogisticsDeliveryType.CREATE]
    client_phone: str
    currency: str
    destination: YangoThirdPartyLogisticsDeliveryLocation
    human_order_id: str
    items: list[YangoThirdPartyLogisticsDeliveryItem]
    order_id: str
    origin: YangoStoreLocation
    additional_phone_code: str | None = None
    delivery_time: int | None = None
    left_at_door: bool | None = None
    meet_outside: bool | None = None
    no_door_call: bool | None = None
    store_id: str | None = None
    total_price: str | None = None


@dataclass(kw_only=True)
class YangoThirdPartyLogisticsDeliveryCancelled:
    type: Literal[YangoThirdPartyLogisticsDeliveryType.CANCEL]
    reason: str | None = None


@dataclass(kw_only=True)
class YangoThirdPartyLogisticsDeliveryEvent:
    data: YangoThirdPartyLogisticsDeliveryCreated | YangoThirdPartyLogisticsDeliveryCancelled
    delivery_id: int
    occurred: str


@dataclass(kw_only=True)
class YangoThirdPartyLogisticsDeliveryEvents:
    events: list[YangoThirdPartyLogisticsDeliveryEvent]
    cursor: str


class YangoThirdPartyLogisticsDeliveryStatus(str, Enum):
    SCHEDULED = 'scheduled'
    MATCHING = 'matching'
    OFFERED = 'offered'
    MATCHED = 'matched'
    DELIVERING = 'delivering'
    DELIVERY_ARRIVED = 'delivery_arrived'
    DELIVERED = 'delivered'
    CANCELED = 'canceled'


@dataclass(kw_only=True)
class YangoThirdPartyLogisticsDeliveryCourierName:
    first_name: str
    patronymic: str | None = None
    surname: str | None = None


@dataclass(kw_only=True)
class YangoThirdPartyLogisticsDeliveryCourierInfo:
    id: str
    name: YangoThirdPartyLogisticsDeliveryCourierName
    phone: str
    legal_entity: str | None = None
    car_color: str | None = None
    car_color_hex: str | None = None
    car_model: str | None = None
    car_number: str | None = None
    phone_extension: str | None = None
    transport_type: str | None = None


@dataclass(kw_only=True)
class YangoThirdPartyLogisticsDeliveryCourierPosition:
    location: Point
    timestamp: str
    direction: float | None = None
    speed: float | None = None
