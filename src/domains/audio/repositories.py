from abc import ABC, abstractmethod
from typing import Optional

from .entities import AudioFile


class AudioRepository(ABC):
    @abstractmethod
    async def save(self, audio_file: AudioFile) -> AudioFile:
        pass

    @abstractmethod
    async def get_by_id(self, file_id: str) -> Optional[AudioFile]:
        pass

    @abstractmethod
    async def update(self, audio_file: AudioFile) -> AudioFile:
        pass

    @abstractmethod
    async def delete(self, file_id: str) -> None:
        pass