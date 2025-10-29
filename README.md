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
pip install yango-tech-grocery-client
```

## Quick Start

### Basic Setup

```python
import asyncio
from yango_tech_grocery_client import YangoClient

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

For comprehensive examples, see [EXAMPLES.md](EXAMPLES.md).

## Configuration

### Client Initialization Options

```python
client = YangoClient(
    domain="https://api.retailtech.yango.com",  # API domain
    auth_token="your_auth_token",           # Authentication token
)
```

### Environment Variables

You can also configure the client using environment variables:

```bash
export YANGO_DOMAIN="https://api.retailtech.yango.com"
export YANGO_AUTH_TOKEN="your_auth_token"
```

## Documentation

- **[EXAMPLES.md](https://github.com/yango-tech/yango-tech-grocery-client/blob/main/EXAMPLES.md)** - Comprehensive usage examples
- **[DEVELOPMENT.md](https://github.com/yango-tech/yango-tech-grocery-client/blob/main/DEVELOPMENT.md)** - Development and contribution guide
