from decimal import Decimal
import os

import requests
from examples.constants import URL
from examples.signing import sign_auth_headers
from web3 import Account

def withdraw(withdrawal_amount: Decimal, currency: str):
    """
    Triggers the withdrawal for the given amount and token from the clearinghouse contract.

    :param withdrawal_amount: 
        The amount to withdraw. Eg. if you want to withdraw 2.3 ETH, you would pass 2.3.
        Has to be a Decimal to avoid floating point issues.
    :param currency: 
        The symbol of the currency to withdraw, eg WETH.
    """

    # User must set private key
    account = Account.from_key(os.environ["TAKER_PRIVATE_KEY"])

    # First sign the auth headers
    headers = sign_auth_headers(account=account)
    print(f"Headers: {headers}")

    # Create deposit request payload
    payload = {
        "account": account.address,
        "amount": str(withdrawal_amount),
        "currency": currency,
    }

    # Send deposit request
    response = requests.post(f"http://{URL}/withdraw", json=payload, headers=headers)
    response.raise_for_status()
    print(response.json())


if __name__ == "__main__":
    withdraw(Decimal("2.3"), "ALPHA")
