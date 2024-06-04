import asyncio
from typing import Any
import uuid
import random

import orjson as json

from .base import WebSocketClient


class OrderClient(WebSocketClient):
    def __init__(self, uri, headers, force_buying: bool = False):
        super().__init__(uri, headers)
        self.force_buying = force_buying

    async def handle_message(self, message):
        data = json.loads(message)
        message_type = data.get('type')
        print(f"Recieved handle_message: {data}")
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
                    'pool_id': 'ETH-USD_common', 
                    'sequence_number': 300, 
                    'symbol': 'ETH-USD', 
                    'bids': ['100', '99', '98', '97', '96', '95'], 
                    'offers': ['101', '102', '103', '104', '105', '106'], 
                    'sizes': ['0.1', '0.5', '1', '5', '10', '20']
                }
            }

            QuoteResponse:
            {
                "type": "quoteresponse",
                "data": {
                    'pool_id': 'ETH-USD_common', 
                    'price': '99.99', 
                    'quantity': '0.1', 
                    'quote_resp_id': 'quote_response_id', 
                    'side': 'SELL', 
                    'symbol': 'ETH-USD', 
                    'sending_time': 1712784773.339189, 
                    'wallet_id': 'taker_wallet'
                }
            }
        """
        await asyncio.sleep(2.5)  # Simulate decision time
        print(f"Data info: type(data)={type(data)} - {data}")
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
                'pool_id': 'ETH-USD_common', 
                'price': price, 
                'quantity': quantity,
                'quote_resp_id': str(uuid.uuid4()), 
                'side': side, 
                'symbol': 'ETH-USD', 
                'sending_time': self.now, 
                'wallet_id': self.wallet
            }
        }
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
                    'pool_id': 'ETH-USD_common', 
                    'price': '100.77', 
                    'quantity': '0.1', 
                    'quote_id': 'quote_response_id', 
                    'side': 'BUY',
                    'status': 'REJECT', 
                    'symbol': 'ETH-USD', 
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
        print(f"Taker trade message received: {data}")
