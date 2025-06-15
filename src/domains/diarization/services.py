from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union, Dict

from .entities import Diarization, DiarizationStatus


class DiarizationService(ABC):
    @abstractmethod
    async def create_diarization_task(
        self, audio_file_id: str, user_id: int, num_speakers: Optional[int] = None
    ) -> Diarization:
        """Create a new diarization task"""
        pass

    @abstractmethod
    async def diarize(self, diarization_id: str) -> Diarization:
        """Process diarization task"""
        pass

    @abstractmethod
    async def get_diarization(self, diarization_id: str) -> Optional[Diarization]:
        """Get diarization by ID"""
        pass

    @abstractmethod
    async def estimate_num_speakers(self, audio_path: Path) -> int:
        """Estimate the number of speakers in the audio file"""
        pass

    @abstractmethod
    async def merge_with_transcription(
        self, diarization_id: str, transcription_id: str
    ) -> Dict[str, Union[str, List[Dict]]]:
        """Merge diarization with transcription to get speaker-labeled transcription"""
        pass