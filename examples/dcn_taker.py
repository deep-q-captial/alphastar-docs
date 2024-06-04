import os

from web3 import Account

from examples.signing import sign_auth_headers
from examples.websocket.base import WebSocketClientManager
from examples.websocket.marketdata import MarketDataClient
from examples.websocket.taker import OrderClient


def main():
    # User must set

    account = Account.from_key(os.environ["TAKER_PRIVATE_KEY"])

    # First sign the auth headers
    headers = sign_auth_headers(account=account)
    print(f"Headers: {headers}")

    # Create an OrderClient that can act on market data and place orders and listen for trades
    order_client = OrderClient(
        uri="ws://localhost:8000/ws/taker",
        headers=headers
    )

    # Set the order client to handle responses from the market data client
    market_data_client = MarketDataClient(
        uri="ws://localhost:8000/ws/mktdata",
        headers=headers,
        message_handler=order_client.handle_quote
    )

    # Add the clients to the manager
    manager = WebSocketClientManager()
    manager.add_client('marketdata', market_data_client)
    manager.add_client('taker', order_client)

    # Run the clients
    manager.run()


if __name__ == "__main__":
    main()
