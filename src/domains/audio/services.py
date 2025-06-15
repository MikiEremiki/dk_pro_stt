from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional, List, Tuple

from .entities import AudioFile, AudioFormat


class AudioService(ABC):
    @abstractmethod
    async def validate_audio(self, file: BinaryIO, filename: str, user_id: int) -> AudioFile:
        """Validate audio file and create AudioFile entity"""
        pass

    @abstractmethod
    async def convert_to_wav(self, audio_file: AudioFile) -> Path:
        """Convert audio to WAV format for processing"""
        pass

    @abstractmethod
    async def get_audio_duration(self, file_path: Path) -> float:
        """Get audio duration in seconds"""
        pass

    @abstractmethod
    async def normalize_volume(self, file_path: Path) -> Path:
        """Normalize audio volume"""
        pass

    @abstractmethod
    async def detect_silence(self, file_path: Path) -> List[Tuple[float, float]]:
        """Detect silence periods in audio file"""
        pass