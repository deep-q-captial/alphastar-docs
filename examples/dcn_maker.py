import os

from web3 import Account

from examples.signing import sign_auth_headers
from examples.websocket.base import WebSocketClientManager
from examples.websocket.maker import MakerClient


def main():

    account = Account.from_key(os.environ["MAKER_PRIVATE_KEY"])

    # First sign the auth headers
    headers = sign_auth_headers(account=account)
    print(f"Headers: {headers}")

    # Create a MakerClient that can publish Quotes
    maker_client = MakerClient(
        uri="ws://localhost:8000/ws/maker",
        headers=headers,
        pool_id="ETH-USD_common",
    )

    # Add the clients to the manager
    manager = WebSocketClientManager()
    manager.add_client('maker', maker_client)

    # Run the clients
    manager.run()


if __name__ == "__main__":
    main()
