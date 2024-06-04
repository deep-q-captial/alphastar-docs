import asyncio
import websockets
import random
import uuid
from decimal import Decimal

import orjson as json
from .base import WebSocketClient


class MakerClient(WebSocketClient):
    """A WebSocket client for simulating a market maker.
    """

    def __init__(self, uri, headers, pool_id: str = "ETH-USD_common", valid_until_time: int = 5) :
        """
        Initialize the MakerClient with given parameters.

        Args:
            uri (str): WebSocket server URI.
            headers (dict): Headers for WebSocket connection.
            pool_id (str): Identifier for the trading pool.
            valid_until_time (int): Validity duration for quotes.
        """
        super().__init__(uri, headers)
        self.pool_id = pool_id
        self.valid_until_time = valid_until_time

        # Market making parameters
        self.true_mid = Decimal('100.00')
        self.true_mu = 0
        self.true_sigma = 0.20
        
        # Quote time generation
        self.quote_every_sec = 5
        self.quote_every_mu = 10
        self.quote_every_sigma = 2

        # Quote randomised bid/ask spread generation
        self.spread_mu = 0.05
        self.spread_sigma = 0.01

        # NOTE: Sizes are fixed per stream see liquidity_levels REST endpoint
        self.size_premium = {
            "0.1": Decimal("0.0"), 
            "0.5": Decimal("0.01"), 
            "1": Decimal("0.02"), 
            "5": Decimal("0.05"), 
            "10": Decimal("0.10"), 
            "20": Decimal("0.15")
        }

    async def simulate_true_mid(self):       
        """Periodically update the true mid price based on a normal distribution.
        """
        while True:
            await asyncio.sleep(self.quote_every_sec)
            self.true_mid += Decimal(f"{random.gauss(self.true_mu, self.true_sigma):.2f}")

    async def simulate_quotes(self):
        """Periodically generate and send quotes to the WebSocket server.
        """
        while True:
            await asyncio.sleep(random.gauss(self.quote_every_mu, self.quote_every_sigma))

            bid = self.true_mid - Decimal(f"{max(0, random.gauss(self.spread_mu, self.spread_sigma)):.2f}")
            bids = [f"{bid + size_premium:.2f}" for size_premium in self.size_premium.values()]
            ask = self.true_mid + Decimal(f"{max(0, random.gauss(self.spread_mu, self.spread_sigma)):.2f}")
            asks = [f"{ask + size_premium:.2f}" for size_premium in self.size_premium.values()]
            
            quote = {
                "type": "quote",
                "data": {
                    "sending_time": self.now,
                    "quote_id": f"{uuid.uuid4()}",
                    "wallet_id": self.wallet,
                    "pool_id": self.pool_id,
                    "bid_px": bids,
                    "offer_px": asks,
                    "valid_until_time": self.valid_until_time
                }
            }
            await self.send_message(json.dumps(quote))

    async def handle_message(self, message):
        """Handle incoming WebSocket messages.

        Args:
            message (str): The incoming WebSocket message.
        """

        data = json.loads(message)
        message_type = data.get('type')
        message = json.loads(data["data"])

        if message_type == 'makertrademessage':
            await self.handle_maker_trade(message)
        else:
            await self.handle_unknown(data)

    async def handle_maker_trade(self, data):
        """Handle trade messages from takers.

        Args:
            data (dict): The trade message data.
            
        For this we simulate the decision-making process to accept or reject the offer. 
        We get several acks on this stream type. 
            1. The MM is offered to deal with a status=REQUEST
            2. The MM responds with a status=ACCEPT or status=REJECTED
            3. The MM is informed of the status of the trade with status=DONE or status=NOT_DONE
        
        makertrademessage:
        {
            "type": "takertrademessage",
            "data": {
                'timestamp': 'float64',
                'match_timestamp': 'float64',
                'wallet_id': 'str',
                'pool_id': 'str',
                'symbol': 'str',
                'trade_id': 'str',
                'taker_wallet_id': 'str',
                'side': 'str',
                'requested_quantity': 'object',
                'requested_price': 'object',
                'quote_price': 'object',
                'quote_quantity': 'object',
                'quote_id': 'str',
                'quote_created_at': 'float64',
                'valid_until_time': 'float64',
                'maker_fee': 'object',
                'maker_fee_ccy': 'str',
                'executed_quantity': 'object',
                'executed_price': 'object',
                'status': 'str',
                'msg': 'str'
            }
        }
        """
        # Handle taker trade messages (filled or rejected)
        print(f"Maker trade message received: {data}")

        if data['status'] == 'REQUEST':    
            # Randomly accept or reject the response
            decision = random.choice([
                dict(status='ACCEPT', msg='Trade Accepted', executed_quantity=data['requested_quantity'], executed_price=data['requested_price']), 
                dict(status='REJECT', msg='Trade Rejected', executed_quantity="0", executed_price="0")
            ])
            data["timestamp"] = self.now
            data.update(decision)
            message = {
                "type": "takertrademessage",
                "data": data
            } 
            await self.send_message(json.dumps(message))
            print(f"Maker trade response sent: {message}")

        elif data["status"] in ["DONE", "NOT_DONE"]:
            pass # Process fills or ignore rejects

    async def connect(self):
        """Connect to the WebSocket server and run the market making simulations.
        """
        async with websockets.connect(self.uri, extra_headers=self.headers) as websocket:
            self.websocket = websocket
            await asyncio.gather(
                self.simulate_true_mid(),
                self.simulate_quotes(),
                self.handle_messages(websocket)  # Add this to listen to incoming messages
            )
