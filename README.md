# Yango Tech Grocery API Client

A Python client library for interacting with the Yango Tech Grocery API. This library provides a comprehensive interface for managing orders, products, prices, stocks, and other grocery-related operations.

## Features

- **Order Management**: Create, update, cancel, and track orders
- **Product Management**: Create and update products, manage product media and VAT
- **Price Management**: Handle price lists, prices, and discounts
- **Stock Management**: Update and retrieve stock information
- **Store Management**: Get store information
- **Receipt Management**: Upload and retrieve receipts
- **Event Handling**: Process order events and state changes
- **Async Support**: Full async/await support for all operations
- **Error Handling**: Comprehensive error handling with retry logic

## Installation

```bash
pip install yango-grocery-client
```

## Quick Start

### Basic Setup

```python
import asyncio
from yango_grocery_client import YangoClient

async def main():
    # Initialize the client
    client = YangoClient(
        domain="https://api.retailtech.yango.com",
        auth_token="your_auth_token_here"
    )
    
    # Your API calls here
    stores = await client.get_stores()
    print(f"Found {len(stores)} stores")

# Run the async function
asyncio.run(main())
```

## API Examples

### Order Management

#### Create an Order

```python
from yango_grocery_client import YangoClient, YangoOrderRecord, YangoShoppingCartItem

async def create_order_example():
    client = YangoClient(domain="https://api.retailtech.yango.com", auth_token="your_token")
    
    # Create shopping cart items
    cart_items = [
        YangoShoppingCartItem(
            product_id="product_123",
            quantity=2,
            price="150.00",
            discount="10.00",
            vat="20.00"
        )
    ]
    
    # Create order record
    order = YangoOrderRecord(
        order_id="order_456",
        store_id="store_789",
        customer_phone="+1234567890",
        customer_name="John Doe",
        delivery_address="123 Main St, City",
        delivery_latitude=55.7558,
        delivery_longitude=37.6176,
        cart_items=cart_items,
        total_price="290.00",
        delivery_fee="50.00",
        payment_method="card"
    )
    
    # Create the order
    result = await client.create_order(order)
    print(f"Order created: {result}")

```

#### Get Order Details

```python
async def get_order_example():
    client = YangoClient(domain="https://api.retailtech.yango.com", auth_token="your_token")
    
    # Get order details
    order_detail = await client.get_order_detail("order_456")
    print(f"Order status: {order_detail['status']}")
    print(f"Order total: {order_detail['total_price']}")

```

#### Cancel an Order

```python
async def cancel_order_example():
    client = YangoClient(domain="https://api.retailtech.yango.com", auth_token="your_token")
    
    # Cancel order with reason
    result = await client.cancel_order(
        order_id="order_456",
        reason="Customer requested cancellation"
    )
    print(f"Order cancelled: {result}")

```

#### Get Orders State

```python
async def get_orders_state_example():
    client = YangoClient(domain="https://api.retailtech.yango.com", auth_token="your_token")
    
    # Get state of multiple orders
    order_ids = ["order_456", "order_789", "order_101"]
    states = await client.get_orders_state(order_ids)
    
    for order_state in states:
        print(f"Order {order_state['order_id']}: {order_state['state']}")

```

### Product Management

#### Get All Products

```python
async def get_products_example():
    client = YangoClient(domain="https://api.retailtech.yango.com", auth_token="your_token")
    
    # Get all active products
    products = await client.get_all_products(only_active=True)
    
    print(f"Found {len(products)} active products")
    for product_id, product in products.items():
        print(f"Product {product_id}: {product.name} - {product.price}")

```

#### Create Products

```python
from yango_grocery_client import YangoProductData, YangoCustomAttributes

async def create_products_example():
    client = YangoClient(domain="https://api.retailtech.yango.com", auth_token="your_token")
    
    # Create product data
    product = YangoProductData(
        product_id="new_product_123",
        name="Fresh Apples",
        description="Sweet and juicy apples",
        price="99.99",
        category_id="fruits",
        barcode="1234567890123",
        weight=0.5,
        unit="kg",
        custom_attributes=YangoCustomAttributes(
            brand="Organic Farm",
            country_of_origin="Poland"
        )
    )
    
    # Create the product
    await client.create_products([product])
    print("Product created successfully")

```

#### Get Product Updates

```python
async def get_product_updates_example():
    client = YangoClient(domain="https://api.retailtech.yango.com", auth_token="your_token")
    
    # Get product updates (streaming)
    async for product in client.get_product_updates():
        print(f"Product update: {product.product_id} - {product.name}")

```

### Price Management

#### Create Price Lists

```python
from yango_grocery_client import YangoPriceListUpdateData

async def create_price_lists_example():
    client = YangoClient(domain="https://api.retailtech.yango.com", auth_token="your_token")
    
    price_list = YangoPriceListUpdateData(
        id="price_list_123",
        name="Regular Prices",
        status="active"
    )
    
    await client.create_price_lists([price_list])
    print("Price list created")

```

#### Get Prices

```python
async def get_prices_example():
    client = YangoClient(domain="https://api.retailtech.yango.com", auth_token="your_token")
    
    # Get prices for specific price lists
    price_list_ids = ["price_list_123", "price_list_456"]
    prices = await client.get_prices(price_list_ids)
    
    for price_list_id, price_data in prices.items():
        print(f"Price list {price_list_id}:")
        for price in price_data:
            print(f"  Product {price.product_id}: {price.price}")

```

### Stock Management

#### Update Stocks

```python
from yango_grocery_client import YangoStockData, YangoStockUpdateMode

async def update_stocks_example():
    client = YangoClient(domain="https://api.retailtech.yango.com", auth_token="your_token")
    
    # Create stock data
    stock = YangoStockData(
        product_id="product_123",
        quantity=100,
        unit="unit"
    )
    
    # Update stocks for a store
    await client.update_stocks(
        wms_store_id="store_789",
        stocks=[stock]
    )
    print("Stocks updated successfully")

```

#### Get Stocks

```python
async def get_stocks_example():
    client = YangoClient(domain="https://api.retailtech.yango.com", auth_token="your_token")
    
    # Get stocks
    stocks = await client.get_stocks()
    print(f"Retrieved {len(stocks['stocks'])} stock records")

```

### Store Management

#### Get Stores

```python
async def get_stores_example():
    client = YangoClient(domain="https://api.retailtech.yango.com", auth_token="your_token")
    
    # Get all stores
    stores = await client.get_stores()
    
    for store in stores:
        print(f"Store {store.store_id}: {store.name}")
        print(f"  Address: {store.address}")
        print(f"  Coordinates: {store.latitude}, {store.longitude}")

```

### Receipt Management

#### Upload Receipt

```python
async def upload_receipt_example():
    client = YangoClient(domain="https://api.retailtech.yango.com", auth_token="your_token")
    
    # Upload receipt document (PDF)
    with open("receipt.pdf", "r") as f:
        document_content = f.read()
    
    await client.upload_receipt(
        receipt_id="receipt_123",
        document=document_content
    )
    print("Receipt uploaded successfully")

```

#### Get Receipt

```python
async def get_receipt_example():
    client = YangoClient(domain="https://api.retailtech.yango.com", auth_token="your_token")
    
    # Get receipt details
    receipt = await client.get_receipt("receipt_123")
    print(f"Receipt amount: {receipt.amount}")
    print(f"Receipt status: {receipt.status}")

```

### Event Handling

#### Get Order Events

```python
async def get_order_events_example():
    client = YangoClient(domain="https://api.retailtech.yango.com", auth_token="your_token")
    
    # Get order events
    events_response = await client.get_orders_events_query()
    
    print(f"Next cursor: {events_response.cursor}")
    for event in events_response.orders_events:
        print(f"Order {event.order_id}: {event.data.type} at {event.occurred}")

```

### Error Handling

```python
from yango_grocery_client import YangoBadRequest, YangoRequestError

async def error_handling_example():
    client = YangoClient(domain="https://api.retailtech.yango.com", auth_token="your_token")
    
    try:
        # This might fail if order doesn't exist
        order = await client.get_order_detail("non_existent_order")
    except YangoBadRequest as e:
        print(f"Bad request error: {e.message}")
        print(f"Error details: {e.payload}")
    except YangoRequestError as e:
        print(f"Request error: {e.message}")
        print(f"Status code: {e.status}")

```

## Configuration

### Client Initialization Options

```python
client = YangoClient(
    domain="https://api.retailtech.yango.com",  # API domain
    auth_token="your_auth_token",           # Authentication token
    error_handler=custom_error_handler,     # Optional custom error handler
    proxy="http://proxy.example.com:8080"   # Optional proxy configuration
)
```

### Environment Variables

You can also configure the client using environment variables:

```bash
export YANGO_DOMAIN="https://api.retailtech.yango.com"
export YANGO_AUTH_TOKEN="your_auth_token"
```