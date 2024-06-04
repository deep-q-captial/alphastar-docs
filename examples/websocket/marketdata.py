import orjson as json

from .base import WebSocketClient


class MarketDataClient(WebSocketClient):
    """A WebSocket client for handling market data messages.
    """

    def __init__(self, uri: str, headers: dict[str, str], message_handler: callable = None):
        """Initialize the MarketDataClient with given parameters.

        Args:
            uri (str): WebSocket server URI.
            headers (dict): Headers for WebSocket connection.
            message_handler (Callable, optional): Function to handle incoming market data messages.
        """
        super().__init__(uri, headers)
        self.message_handler = message_handler

    async def handle_message(self, message):
        """Handle incoming WebSocket messages.

        Args:
            message (str): The incoming WebSocket message.
        """
        data = json.loads(message)
        message_type = data.get('type')
        message = json.loads(data["data"])

        if message_type == 'marketdata':
            if self.message_handler:
                await self.message_handler(message)
        elif message_type == 'alphastarheartbeat':
            await self.handle_heartbeat(message)
        else:
            await self.handle_unknown(data)
