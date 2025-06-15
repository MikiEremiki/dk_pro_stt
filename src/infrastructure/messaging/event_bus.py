import json
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from nats.aio.msg import Msg

from .nats_client import NatsConnection

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Event:
    """Base class for all events."""
    
    @classmethod
    def event_name(cls) -> str:
        """Get the event name."""
        return cls.__name__
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return self.__dict__
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary."""
        return cls(**data)


class EventBus(ABC):
    """Event bus interface."""
    
    @abstractmethod
    async def publish(self, event: Event) -> None:
        """Publish an event."""
        pass
    
    @abstractmethod
    async def subscribe(self, event_type: Type[Event], handler: Callable[[Event], None]) -> None:
        """Subscribe to an event type."""
        pass
    
    @abstractmethod
    async def unsubscribe_all(self) -> None:
        """Unsubscribe from all events."""
        pass


class NatsEventBus(EventBus):
    """NATS implementation of event bus."""
    
    def __init__(self, nats_connection: NatsConnection, subject_prefix: str = "events"):
        self.nats = nats_connection
        self.subject_prefix = subject_prefix
        self.subscriptions: Dict[str, List[int]] = {}
    
    def _get_subject(self, event_type: Type[Event]) -> str:
        """Get the NATS subject for an event type."""
        return f"{self.subject_prefix}.{event_type.event_name()}"
    
    async def publish(self, event: Event) -> None:
        """Publish an event to NATS."""
        subject = self._get_subject(type(event))
        payload = {
            "event_type": type(event).__name__,
            "data": event.to_dict()
        }
        await self.nats.publish(subject, payload)
        logger.debug(f"Published event {type(event).__name__} to {subject}")
    
    async def subscribe(self, event_type: Type[Event], handler: Callable[[Event], None]) -> None:
        """Subscribe to an event type."""
        subject = self._get_subject(event_type)
        
        async def message_handler(msg: Msg) -> None:
            try:
                payload = json.loads(msg.data.decode())
                event_data = payload.get("data", {})
                event = event_type.from_dict(event_data)
                await handler(event)
            except Exception as e:
                logger.error(f"Error handling event {event_type.__name__}: {e}")
        
        sid = await self.nats.subscribe(subject, message_handler)
        
        if subject not in self.subscriptions:
            self.subscriptions[subject] = []
        self.subscriptions[subject].append(sid)
        
        logger.info(f"Subscribed to event {event_type.__name__} on {subject}")
    
    async def unsubscribe_all(self) -> None:
        """Unsubscribe from all events."""
        for subject, sids in self.subscriptions.items():
            for sid in sids:
                await self.nats.unsubscribe(sid)
            logger.info(f"Unsubscribed from {subject}")
        self.subscriptions = {}


# Example event classes
class AudioProcessedEvent(Event):
    """Event emitted when audio processing is complete."""
    
    def __init__(self, audio_id: str, user_id: int, success: bool, error_message: Optional[str] = None):
        self.audio_id = audio_id
        self.user_id = user_id
        self.success = success
        self.error_message = error_message


class TranscriptionCompletedEvent(Event):
    """Event emitted when transcription is complete."""
    
    def __init__(self, transcription_id: str, audio_id: str, user_id: int, success: bool, error_message: Optional[str] = None):
        self.transcription_id = transcription_id
        self.audio_id = audio_id
        self.user_id = user_id
        self.success = success
        self.error_message = error_message


class DiarizationCompletedEvent(Event):
    """Event emitted when diarization is complete."""
    
    def __init__(self, diarization_id: str, audio_id: str, user_id: int, success: bool, error_message: Optional[str] = None):
        self.diarization_id = diarization_id
        self.audio_id = audio_id
        self.user_id = user_id
        self.success = success
        self.error_message = error_message


class ExportCompletedEvent(Event):
    """Event emitted when export is complete."""
    
    def __init__(self, export_id: str, user_id: int, success: bool, file_url: Optional[str] = None, error_message: Optional[str] = None):
        self.export_id = export_id
        self.user_id = user_id
        self.success = success
        self.file_url = file_url
        self.error_message = error_message