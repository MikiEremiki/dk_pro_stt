import json
import logging
from typing import Any, Callable, Dict, Optional, List

import nats
from nats.aio.client import Client as NatsClient
from nats.aio.msg import Msg

logger = logging.getLogger(__name__)


class NatsConnection:
    """NATS connection manager."""

    def __init__(self, nats_url: str):
        self.nats_url = nats_url
        self.client: Optional[NatsClient] = None
        self.subscriptions: List[int] = []

    async def connect(self) -> None:
        """Connect to NATS server."""
        if self.client and self.client.is_connected:
            return

        self.client = await nats.connect(self.nats_url)
        logger.info(f"Connected to NATS server at {self.nats_url}")

    async def disconnect(self) -> None:
        """Disconnect from NATS server."""
        if self.client and self.client.is_connected:
            for sid in self.subscriptions:
                await self.client.unsubscribe(sid)
            await self.client.close()
            self.client = None
            self.subscriptions = []
            logger.info("Disconnected from NATS server")

    async def publish(self, subject: str, payload: Dict[str, Any]) -> None:
        """Publish a message to a subject."""
        if not self.client or not self.client.is_connected:
            await self.connect()

        message = json.dumps(payload).encode()
        await self.client.publish(subject, message)
        logger.debug(f"Published message to {subject}: {payload}")

    async def subscribe(self, subject: str, callback: Callable[[Msg], None]) -> int:
        """Subscribe to a subject."""
        if not self.client or not self.client.is_connected:
            await self.connect()

        sid = await self.client.subscribe(subject, cb=callback)
        self.subscriptions.append(sid)
        logger.info(f"Subscribed to {subject} with sid {sid}")
        return sid

    async def unsubscribe(self, sid: int) -> None:
        """Unsubscribe from a subscription."""
        if not self.client or not self.client.is_connected:
            return

        await self.client.unsubscribe(sid)
        if sid in self.subscriptions:
            self.subscriptions.remove(sid)
        logger.info(f"Unsubscribed from sid {sid}")

    async def request(self, subject: str, payload: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
        """Send a request and wait for a response."""
        if not self.client or not self.client.is_connected:
            await self.connect()

        message = json.dumps(payload).encode()
        response = await self.client.request(subject, message, timeout=timeout)
        return json.loads(response.data.decode())