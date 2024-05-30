import json
import os

from dotenv import load_dotenv
from eth_account.messages import encode_defunct
from web3 import Account

account = None


def get_account() -> Account:
    """
    Loads the private key from the .env file and creates an Account
    object that can be used to sign transactions and messages.
    """
    global account
    if account is None:
        load_dotenv()
        account = Account.from_key(os.getenv("WALLET_PRIVATE_KEY"))

    return account


def sign_auth_headers(data: dict = {}):
    """
    Signs the given data with your wallet to authenticate requests to the API.
    """

    account = get_account()

    data_enc = encode_defunct(json.dumps(data))
    data_enc = account.sign_message(data_enc)

    return {"wallet": account.address, "signature": data_enc.signature.hex()}
