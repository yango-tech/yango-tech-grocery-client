#!/usr/bin/env python3
"""
Command-line interface for Yango Grocery Client.
"""

import argparse
import asyncio
import sys
from typing import TYPE_CHECKING

from .client import YangoClient
from .constants import DEFAULT_DOMAIN

if TYPE_CHECKING:
    from .schema import YangoThirdPartyLogisticsDeliveryType


async def get_stores(domain: str, auth_token: str) -> None:
    """Get and display all stores."""
    client = YangoClient(domain=domain, auth_token=auth_token)
    try:
        stores = await client.get_stores()
        print(f'Found {len(stores)} stores:')
        for store in stores:
            print(f'  - {store.id}: {store.name}')
            print(f'    Address: {store.address}')
            print(f'    Coordinates: {store.location.lat}, {store.location.lon}')
    except Exception as e:
        print(f'Error getting stores: {e}', file=sys.stderr)
        sys.exit(1)


async def get_products(domain: str, auth_token: str, only_active: bool = True) -> None:
    """Get and display products."""
    client = YangoClient(domain=domain, auth_token=auth_token)
    try:
        products = await client.get_all_products(only_active=only_active)
        print(f'Found {len(products)} {"active " if only_active else ""}products:')
        for product_id, product in products.items():
            print(f'  - {product_id}:')
            print(f'    Master category: {product.master_category}')
            print(f'    Status: {product.status}')
    except Exception as e:
        print(f'Error getting products: {e}', file=sys.stderr)
        sys.exit(1)


async def get_order_detail(domain: str, auth_token: str, order_id: str) -> None:
    """Get and display order details."""
    client = YangoClient(domain=domain, auth_token=auth_token)
    try:
        order = await client.get_order_detail(order_id)
        print(f'Order {order_id}:')
        print(f'  Cart: {order.cart}')
        print(f'  Delivery Address: {order.delivery_address}')
        print(f'  Store ID: {order.store_id}')
        print(f'  Delivery Properties: {order.delivery_properties}')
    except Exception as e:
        print(f'Error getting order details: {e}', file=sys.stderr)
        sys.exit(1)


async def get_3pl_events(domain: str, auth_token: str, cursor: str | None = None, limit: int | None = None) -> None:
    """Get and display 3PL delivery events summary."""
    client = YangoClient(domain=domain, auth_token=auth_token)
    try:
        events_response = await client.get_deliveries_events(cursor=cursor, limit=limit)

        event_counts: dict[YangoThirdPartyLogisticsDeliveryType, int] = {}
        for event in events_response.events:
            event_type = event.data.type
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        print(f'Found {len(events_response.events)} 3PL delivery events:')
        print(f'Cursor: {events_response.cursor}')
        print()

        if event_counts:
            print('Event types summary:')
            for event_type, count in sorted(event_counts.items()):
                print(f'  {event_type}: {count}')
        else:
            print('No events found.')
    except Exception as e:
        print(f'Error getting 3PL events: {e}', file=sys.stderr)
        sys.exit(1)


async def update_delivery_status(domain: str, auth_token: str, delivery_id: int, status: str) -> None:
    """Update delivery status."""
    from .schema import YangoThirdPartyLogisticsDeliveryStatus

    client = YangoClient(domain=domain, auth_token=auth_token)
    try:
        delivery_status = YangoThirdPartyLogisticsDeliveryStatus(status)
        await client.update_delivery_status(delivery_id, delivery_status)
        print(f'Successfully updated delivery {delivery_id} status to {status}')
    except ValueError:
        print(
            f'Invalid status "{status}". Valid statuses: {[s.value for s in YangoThirdPartyLogisticsDeliveryStatus]}',
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(f'Error updating delivery status: {e}', file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Yango Grocery API Client CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  %(prog)s stores --domain {DEFAULT_DOMAIN} --token YOUR_TOKEN
  %(prog)s products --domain {DEFAULT_DOMAIN} --token YOUR_TOKEN
  %(prog)s order --domain {DEFAULT_DOMAIN} --token YOUR_TOKEN --order-id ORDER_123
  %(prog)s 3pl-events --domain {DEFAULT_DOMAIN} --token YOUR_TOKEN
  %(prog)s 3pl-events --domain {DEFAULT_DOMAIN} --token YOUR_TOKEN --limit 10 --cursor CURSOR_VALUE
  %(prog)s 3pl-update-delivery-status --domain {DEFAULT_DOMAIN} --token YOUR_TOKEN --delivery-id 123 --status matched
        """,
    )

    parser.add_argument('--domain', required=True, help=f'Yango API domain (e.g., {DEFAULT_DOMAIN})')
    parser.add_argument('--token', required=True, help='Authentication token')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Stores command
    subparsers.add_parser('stores', help='Get all stores')

    # Products command
    products_parser = subparsers.add_parser('products', help='Get products')
    products_parser.add_argument('--all', action='store_true', help='Include inactive products')

    # Order command
    order_parser = subparsers.add_parser('order', help='Get order details')
    order_parser.add_argument('--order-id', required=True, help='Order ID to retrieve')

    # 3PL - Events command
    events_parser = subparsers.add_parser('3pl-events', help='Get 3PL delivery events')
    events_parser.add_argument('--cursor', help='Cursor for pagination')
    events_parser.add_argument('--limit', type=int, help='Limit number of events to retrieve')

    # 3PL - Update delivery status command
    status_parser = subparsers.add_parser('3pl-update-delivery-status', help='Update delivery status')
    status_parser.add_argument('--delivery-id', type=int, required=True, help='Delivery ID to update')
    status_parser.add_argument('--status', required=True, help='New delivery status')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Run the appropriate command
    if args.command == 'stores':
        asyncio.run(get_stores(args.domain, args.token))
    elif args.command == 'products':
        asyncio.run(get_products(args.domain, args.token, not args.all))
    elif args.command == 'order':
        asyncio.run(get_order_detail(args.domain, args.token, args.order_id))
    elif args.command == '3pl-events':
        asyncio.run(get_3pl_events(args.domain, args.token, args.cursor, args.limit))
    elif args.command == '3pl-update-delivery-status':
        asyncio.run(update_delivery_status(args.domain, args.token, args.delivery_id, args.status))


if __name__ == '__main__':
    main()
