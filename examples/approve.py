from decimal import Decimal
import time

import requests
from eth_abi import abi

from examples.constants import ARBITRUM_SEPOLIA_CHAIN_ID, CLEARINGHOUSE, RPC_URL, TOKENS
from examples.signing import get_account


def get_nonce(address: str) -> int:
    """
    Gets the nonce for the given wallet address from the blockchain.
    """

    request = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "eth_getTransactionCount",
        "params": [address, "latest"]
    }

    response = requests.post(RPC_URL, json=request).json()
    if "error" in response:
        raise ValueError(response["error"])

    return int(response["result"], 16)


def approve(deposit_amount: Decimal, currency: str):
    """
    Creates and executes an approval transaction for the given amount and token.

    This approval is required before you can request a deposit via the API,
    in order to allow the clearinghouse contract to pull the funds from your wallet.

    The approach in here is a very low-level way to send transactions, which has the
    advantage that you can easily switch out transport layers (eg. different http libraries).
    Alternatively, you can make use of the `web3` library to execute the approval.

    :param deposit_amount: 
        The amount to approve. Eg. if you want to approve a deposit of 2.3 ETH, you would pass 2.3.
        Has to be a Decimal to avoid floating point issues.
    :param currency: 
        The symbol of the currency to approve, eg WETH.
    """

    # Cast deposit amount to amount in WEI
    decimals = TOKENS[currency]["decimals"]
    amount_wei = int((deposit_amount * Decimal(10) ** Decimal(decimals)).to_integral_value())

    # Create transaction data
    encoded_function_signature = '0x095ea7b3'
    encoded_params = abi.encode(["address", "uint256"], [CLEARINGHOUSE.lower(), amount_wei]).hex()
    encoded_data = encoded_function_signature + encoded_params

    # Create and sign transaction
    account = get_account()
    transaction = {
        "gas": 2_000_000,
        "gasPrice": 3_000_000_000,
        "nonce": get_nonce(account.address),
        "to": TOKENS[currency]["address"],
        "value": hex(0),
        "chainId": ARBITRUM_SEPOLIA_CHAIN_ID,
        "data": encoded_data
    }
    signed_transaction = account.sign_transaction(transaction)
    transaction_hash = signed_transaction.hash.hex()

    # Create transaction request
    request = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "eth_sendRawTransaction",
        "params": [signed_transaction.rawTransaction.hex()]
    }

    # Send transaction
    response = requests.post(RPC_URL, json=request)
    response.raise_for_status()
    if "error" in response:
        raise ValueError(response["error"])
    print(f"Submitted approval transaction, transaction_hash={transaction_hash}")

    # Poll transaction receipt
    receipt = None
    while receipt is None:
        print("Checking transaction status...")
        request = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "eth_getTransactionReceipt",
            "params": [transaction_hash]
        }
        response = requests.post(RPC_URL, json=request)
        print(response.json())
        if response.status_code == 200:
            response = response.json()

            if "result" in response and response["result"] is not None:
                receipt = response["result"]
                break

        time.sleep(1)
    print(f"Approval transaction done, success={bool(int(receipt['status'], 16))}")


if __name__ == "__main__":
    print(f"Sending DCN approval...")
    approve(Decimal("10000"), "DCN")
