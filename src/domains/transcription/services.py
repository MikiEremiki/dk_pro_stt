from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from .entities import Transcription, TranscriptionModel, TranscriptionSegment


class TranscriptionService(ABC):
    @abstractmethod
    async def create_transcription_task(
        self, audio_file_id: str, user_id: int, model: TranscriptionModel
    ) -> Transcription:
        """Create a new transcription task"""
        pass

    @abstractmethod
    async def transcribe(self, transcription_id: str) -> Transcription:
        """Process transcription task"""
        pass

    @abstractmethod
    async def get_transcription(self, transcription_id: str) -> Optional[Transcription]:
        """Get transcription by ID"""
        pass

    @abstractmethod
    async def detect_language(self, audio_path: Path) -> str:
        """Detect language of the audio file"""
        pass