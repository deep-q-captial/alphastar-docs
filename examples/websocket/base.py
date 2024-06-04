import asyncio
import websockets
import time
from typing import Any


class WebSocketClient:
    """Base class for WebSocket clients that connect to a server and handle messages.
    """ 
    def __init__(self, uri, headers):
        self.uri = uri
        self.headers = headers
        self.wallet = headers.get("wallet")
        if not self.wallet:
            raise ValueError("Wallet address is required as part of Header for authentication")
        self.websocket = None
        self.last_heartbeat = time.time()

    async def connect(self):
        async with websockets.connect(self.uri, extra_headers=self.headers) as websocket:
            self.websocket = websocket
            await self.handle_messages(websocket)

    async def handle_messages(self, websocket):
        async for message in websocket:
            await self.handle_message(message)

    async def handle_message(self, message: Any):
        raise NotImplementedError("This method should be overridden by subclasses")

    async def send_message(self, message: str):
        if self.websocket:
            try:
                print(f"About to send message {message}")
                await self.websocket.send(message)
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"WebSocket connection closed while sending message: {e}")

    async def handle_heartbeat(self, data: dict[str,Any]):
        # Handle heartbeat messages
        timediff = data['timestamp'] - self.last_heartbeat
        self.last_heartbeat = time.time()
        print(f"Heartbeat received: {self.last_heartbeat}, timediff: {timediff}")

    async def handle_unknown(self, data):
        # Handle unknown messages
        raise ValueError(f"Unknown message received: {data}")
    
    @property
    def now(self):
        return time.time()


class WebSocketClientManager:
    """Manages multiple WebSocket clients and starts/stops them.
    """
    def __init__(self):
        self.clients = {}
        self._client_tasks = []

    def add_client(self, name, client):
        self.clients[name] = client

    async def start(self):
        self._client_tasks = [asyncio.create_task(client.connect()) for client in self.clients.values()]
        results = await asyncio.gather(*self._client_tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                print(f"Exception during client execution: {result}")
    
    async def stop(self):
        for task in self._client_tasks:
            task.cancel()
        results = await asyncio.gather(*self._client_tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, asyncio.CancelledError):
                print(f"Task was cancelled: {result}")
            elif isinstance(result, Exception):
                print(f"Exception during task cancellation: {result}")

    def run(self, loop: asyncio.AbstractEventLoop = None):
        if not loop:
            loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.start())
        except KeyboardInterrupt:
            print("Interrupt detected...")
        finally:
            print("Stopping clients...")
            loop.run_until_complete(self.stop())
            print("Closing connection...")
            loop.close()
