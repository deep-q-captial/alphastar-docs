import asyncio
import websockets
import time
from typing import Any
import logging

logger = logging.getLogger(__name__)    




class WebSocketClient:
    """Base class for WebSocket clients that connect to a server and handle messages.
    """ 
    def __init__(self, uri, headers, max_retries=5, retry_delay=5):
        self.uri = uri
        self.headers = headers
        self.wallet = headers.get("wallet")
        if not self.wallet:
            raise ValueError("Wallet address is required as part of Header for authentication")
        self.websocket = None
        self.last_heartbeat = time.time()
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def connect(self):
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                print(f"Attempting to connect to {self.uri} -- attempt number {retry_count}")
                async with websockets.connect(self.uri, extra_headers=self.headers) as websocket:
                    print(f"Connected to {self.uri} with headers: {self.headers}")
                    self.websocket = websocket
                    retry_count = 0  # Reset the retry count on successful connection
                    await self.handle_messages(websocket)
            except (websockets.exceptions.ConnectionClosedError, websockets.exceptions.InvalidURI) as e:
                logging.error(f"Connection closed with error: {e}. Retrying in {self.retry_delay} seconds...")
                retry_count += 1
                await asyncio.sleep(self.retry_delay)
            except Exception as e:
                logging.error(f"Exception during client execution: {e}")
                break  # Break the loop on other exceptions

    async def handle_messages(self, websocket):
        try:
            async for message in websocket:
                await self.handle_message(message)
        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"Connection closed with error. Reconnecting...", exc_info=True)
        except Exception as e:
            logger.error(f"Exception during message handling", exc_info=True)

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
