SERVICE_NAME = 'yango_client'

DEFAULT_BATCH_SIZE = 100
DISCOUNTS_BATCH_SIZE = DEFAULT_BATCH_SIZE
PRICES_BATCH_SIZE = DEFAULT_BATCH_SIZE
PRODUCTS_BATCH_SIZE = DEFAULT_BATCH_SIZE
VAT_BATCH_SIZE = DEFAULT_BATCH_SIZE
STOCKS_BATCH_SIZE = 1000

MAX_RETRIES = 3
ERROR_STATUSES_FOR_RETRY = (429, 500)
RETRY_DELAY = 1  # seconds
DEFAULT_REQUEST_LIMIT = 100
PRODUCTS_REQUEST_LIMIT = 300

MAX_RPS = 5


API_LAYER_STATUS_TO_LEADING_EVENT = {
    'reserving': 'reserving',
    'reserved': 'approving',
    'assembling': 'processing', # sometimes it happens automatically
    'assembled': 'complete',
    'delivering': 'delivering',
    'closed': 'delivered'
}
API_LAYER_STATUSES = tuple(API_LAYER_STATUS_TO_LEADING_EVENT.keys())

WMS_PICKING_EVENTS = set(['reserving', 'approving', 'processing', 'complete'])
LOGISTIC_DELIVERY_EVENTS = set(['delivering', 'delivered'])

REAL_MONEY_PAYMENT_METHODS = ('cash', 'online', 'card', 'apple_pay')

DEFAULT_DOMAIN = "https://api.retailtech.yango.com"
