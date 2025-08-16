#!/usr/bin/env python3
"""
Command-line interface for Yango Grocery Client.
"""

import asyncio
import argparse
import sys

from .client import YangoClient
from .constants import DEFAULT_DOMAIN



async def get_stores(domain: str, auth_token: str) -> None:
    """Get and display all stores."""
    client = YangoClient(domain=domain, auth_token=auth_token)
    try:
        stores = await client.get_stores()
        print(f"Found {len(stores)} stores:")
        for store in stores:
            print(f"  - {store.id}: {store.name}")
            print(f"    Address: {store.address}")
            print(f"    Coordinates: {store.location.lat}, {store.location.lon}")
    except Exception as e:
        print(f"Error getting stores: {e}", file=sys.stderr)
        sys.exit(1)


async def get_products(domain: str, auth_token: str, only_active: bool = True) -> None:
    """Get and display products."""
    client = YangoClient(domain=domain, auth_token=auth_token)
    try:
        products = await client.get_all_products(only_active=only_active)
        print(f"Found {len(products)} {'active ' if only_active else ''}products:")
        for product_id, product in products.items():
            print(f"  - {product_id}:")
            print(f"    Master category: {product.master_category}")
            print(f"    Status: {product.status}")
    except Exception as e:
        print(f"Error getting products: {e}", file=sys.stderr)
        sys.exit(1)


async def get_order_detail(domain: str, auth_token: str, order_id: str) -> None:
    """Get and display order details."""
    client = YangoClient(domain=domain, auth_token=auth_token)
    try:
        order = await client.get_order_detail(order_id)
        print(f"Order {order_id}:")
        print(f"  Status: {order.get('status', 'Unknown')}")
        print(f"  Total Price: {order.get('total_price', 'Unknown')}")
        print(f"  Customer: {order.get('customer_name', 'Unknown')}")
    except Exception as e:
        print(f"Error getting order details: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Yango Grocery API Client CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  %(prog)s stores --domain {DEFAULT_DOMAIN} --token YOUR_TOKEN
  %(prog)s products --domain {DEFAULT_DOMAIN} --token YOUR_TOKEN
  %(prog)s order --domain {DEFAULT_DOMAIN} --token YOUR_TOKEN --order-id ORDER_123
        """
    )
    
    parser.add_argument(
        "--domain",
        required=True,
        help=f"Yango API domain (e.g., {DEFAULT_DOMAIN})"
    )
    parser.add_argument(
        "--token",
        required=True,
        help="Authentication token"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Stores command
    subparsers.add_parser("stores", help="Get all stores")
    
    # Products command
    products_parser = subparsers.add_parser("products", help="Get products")
    products_parser.add_argument(
        "--all",
        action="store_true",
        help="Include inactive products"
    )
    
    # Order command
    order_parser = subparsers.add_parser("order", help="Get order details")
    order_parser.add_argument(
        "--order-id",
        required=True,
        help="Order ID to retrieve"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Run the appropriate command
    if args.command == "stores":
        asyncio.run(get_stores(args.domain, args.token))
    elif args.command == "products":
        asyncio.run(get_products(args.domain, args.token, not args.all))
    elif args.command == "order":
        asyncio.run(get_order_detail(args.domain, args.token, args.order_id))


if __name__ == "__main__":
    main()
