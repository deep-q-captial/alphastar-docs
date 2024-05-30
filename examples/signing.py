import json
import os
from time import time

from dotenv import load_dotenv
from eth_account.messages import encode_defunct
from hexbytes import HexBytes
from web3 import Account

account = None


def get_account() -> Account:
    """
    Loads the private key from the .env file and creates an Account
    object that can be used to sign transactions and messages.

    Note that you can load the private key from any source you like
    and replace this function with your own implementation.
    """
    global account
    if account is None:
        load_dotenv()
        account = Account.from_key(os.getenv("WALLET_PRIVATE_KEY"))

    return account


def sign_auth_headers():
    """
    Signs the given data with your wallet to authenticate requests to the API.
    """

    # Get account to sign with
    account = get_account()

    # Sign current timestamp in seconds
    timestamp = int(time())
    data_encoded = encode_defunct(text=str(timestamp))
    signed_message = account.sign_message(data_encoded)

    # Return headers in correct format
    return {"wallet": account.address, "timestamp": timestamp, "signature": signed_message.signature.hex()}
