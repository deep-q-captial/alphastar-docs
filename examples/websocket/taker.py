import asyncio
from typing import Any
import uuid
import random

import orjson as json
import requests
import random

from .base import WebSocketClient
from examples.signing import sign_auth_headers
import time


class OrderClient(WebSocketClient):
    def __init__(self, uri, account, headers, force_buying: bool = False):
        super().__init__(uri, headers)
        self.force_buying = force_buying
        self.account = account

        # logging market data messages
        self.mkt_data_time = 0
        self.mkt_data_count = 0

        print(f"Balances: {self.get_balances(self.account.address)}")

    async def handle_message(self, message):
        data = json.loads(message)
        message_type = data.get('type')
        message = json.loads(data["data"])

        if message_type == 'marketdata':
            await self.handle_quote(message)
        elif message_type == 'takertrademessage':
            await self.handle_taker_trade(message)
        elif message_type == 'alphastarheartbeat':
            await self.handle_heartbeat(message)
        else:
            await self.handle_unknown(data)

    async def handle_quote(self, data: dict[str, Any]):
        """
            MarketData:
            {
                "type": "marketdata",
                "data": {
                    'timestamp': 1.1, 
                    'pool_id': 'DCN-ALPHA_common', 
                    'sequence_number': 300, 
                    'symbol': 'DCN-ALPHA', 
                    'bids': ['100', '99', '98', '97', '96', '95'], 
                    'offers': ['101', '102', '103', '104', '105', '106'], 
                    'sizes': ['0.1', '0.5', '1', '5', '10', '20']
                }
            }

            QuoteResponse:
            {
                "type": "quoteresponse",
                "data": {
                    'pool_id': 'DCN-ALPHA_common', 
                    'price': '99.99', 
                    'quantity': '0.1', 
                    'quote_resp_id': 'quote_response_id', 
                    'side': 'SELL', 
                    'symbol': 'DCN-ALPHA', 
                    'sending_time': 1712784773.339189, 
                    'wallet_id': 'taker_wallet'
                }
            }
        """
        self.mkt_data_count += 1
        print(f"market update received -- {self.mkt_data_count}")
        if time.time() - self.mkt_data_time > 60:
            print(f"Market Updates Processed: {self.mkt_data_count}")
            self.mkt_data_time = time.time()
            self.mkt_data_count = 0

        action_percentage = 0.25
        if random.random() < action_percentage:

            balances = self.get_balances(self.account.address)
            balances = balances['balances']
            bid_price = data['bids'][0]
            ask_price = data['offers'][0]
            quantity  = data['sizes'][0]
            side = random.choice(['BUY', 'SELL'])
            price = bid_price if side == "SELL" else ask_price
            if self.force_buying:
                side = "BUY" # FORCE BUY
                price = 1000  # FORCE PRICE

            quote_response = {
                "type": "quoteresponse",
                "data": {
                    'pool_id': 'DCN-ALPHA_common', 
                    'price': price, 
                    'quantity': quantity,
                    'quote_resp_id': str(uuid.uuid4()), 
                    'side': side, 
                    'symbol': 'DCN-ALPHA', 
                    'sending_time': self.now, 
                    'wallet_id': self.wallet
                }
            }
            print("---------------------------------------------------")
            print(f"Trade Initiated: {side} {quantity} @ {price}")
            print(f"Pre-Trade Balances")
            print(f"DCN -- contract balance: {balances['DCN']['contract_balance']} | balance: {balances['DCN']['balance']} | in flight: {balances['DCN']['in_flight']} | available: {balances['DCN']['available']}")
            print(f"ALPHA -- contract balance: {balances['ALPHA']['contract_balance']} | balance: {balances['ALPHA']['balance']} | in flight: {balances['ALPHA']['in_flight']} | available: {balances['ALPHA']['available']}")
            print("---------------------------------------------------")
            await self.send_message(json.dumps(quote_response))

    async def handle_taker_trade(self, data: dict[str, Any]):
        """
            TakerTradeMessage:
            {
                "type": "takertrademessage",
                "data": {
                    'executed_price': '0.0', 
                    'executed_quantity': '0.0', 
                    'maker_wallet_id': '', 
                    'match_timestamp': 1712784337.795921, 
                    'msg': 'Trade Miss: Price BUY is less than the best offer price 100.85', 
                    'pool_id': 'DCN-ALPHA_common', 
                    'price': '100.77', 
                    'quantity': '0.1', 
                    'quote_id': 'quote_response_id', 
                    'side': 'BUY',
                    'status': 'REJECT', 
                    'symbol': 'DCN-ALPHA', 
                    'taker_fee': '0.0', 
                    'taker_fee_ccy': 'USD', 
                    'taker_timestamp': 1712784337.795392, 
                    'timestamp': 1712784337.795921, 
                    'type': 'TRADE_RESPONSE', 
                    'wallet_id': 'taker_wallet'
                }
            }
        """
        # Handle taker trade messages (filled or rejected)
        print("---------------------------------------------------")
        print(f"Taker trade message received: {data}")
        balances = self.get_balances(self.account.address)
        balances = balances['balances']
        print(f"Post-Trade Balances")
        print(f"DCN -- contract balance: {balances['DCN']['contract_balance']} | balance: {balances['DCN']['balance']} | in flight: {balances['DCN']['in_flight']} | available: {balances['DCN']['available']}")
        print(f"ALPHA -- contract balance: {balances['ALPHA']['contract_balance']} | balance: {balances['ALPHA']['balance']} | in flight: {balances['ALPHA']['in_flight']} | available: {balances['ALPHA']['available']}")
        print("---------------------------------------------------")

    def get_balances(self, wallet_id):
        headers = sign_auth_headers(account=self.account)
        payload = {
            'account': wallet_id
        }
        response = requests.post(f"https://dcn.alpha.deepqdigital.net/balances", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

