from abc import ABC, abstractmethod
from typing import Optional, List

from .entities import Diarization


class DiarizationRepository(ABC):
    @abstractmethod
    async def save(self, diarization: Diarization) -> Diarization:
        pass

    @abstractmethod
    async def get_by_id(self, diarization_id: str) -> Optional[Diarization]:
        pass

    @abstractmethod
    async def get_by_audio_file_id(self, audio_file_id: str) -> List[Diarization]:
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> List[Diarization]:
        pass

    @abstractmethod
    async def update(self, diarization: Diarization) -> Diarization:
        pass

    @abstractmethod
    async def delete(self, diarization_id: str) -> None:
        pass