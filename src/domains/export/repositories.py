from abc import ABC, abstractmethod
from typing import Optional, List

from .entities import Export, ExportFormat


class ExportRepository(ABC):
    @abstractmethod
    async def save(self, export: Export) -> Export:
        pass

    @abstractmethod
    async def get_by_id(self, export_id: str) -> Optional[Export]:
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> List[Export]:
        pass

    @abstractmethod
    async def get_by_transcription_id(self, transcription_id: str) -> List[Export]:
        pass

    @abstractmethod
    async def get_by_diarization_id(self, diarization_id: str) -> List[Export]:
        pass

    @abstractmethod
    async def update(self, export: Export) -> Export:
        pass

    @abstractmethod
    async def delete(self, export_id: str) -> None:
        pass