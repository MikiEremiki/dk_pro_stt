from abc import ABC, abstractmethod
from typing import Optional, List

from .entities import Transcription


class TranscriptionRepository(ABC):
    @abstractmethod
    async def save(self, transcription: Transcription) -> Transcription:
        pass

    @abstractmethod
    async def get_by_id(self, transcription_id: str) -> Optional[Transcription]:
        pass

    @abstractmethod
    async def get_by_audio_file_id(self, audio_file_id: str) -> List[Transcription]:
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> List[Transcription]:
        pass

    @abstractmethod
    async def update(self, transcription: Transcription) -> Transcription:
        pass

    @abstractmethod
    async def delete(self, transcription_id: str) -> None:
        pass