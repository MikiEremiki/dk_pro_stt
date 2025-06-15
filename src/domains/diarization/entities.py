from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class DiarizationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SpeakerSegment:
    speaker_id: int
    start_time: float  # in seconds
    end_time: float  # in seconds
    confidence: float


@dataclass
class Diarization:
    id: str
    audio_file_id: str
    user_id: int
    status: DiarizationStatus
    num_speakers: Optional[int] = None
    segments: List[SpeakerSegment] = None
    error_message: Optional[str] = None