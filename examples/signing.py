import os

from dotenv import load_dotenv
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
