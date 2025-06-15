from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class TranscriptionModel(str, Enum):
    WHISPER_LARGE_V3 = "whisper-large-v3"
    WHISPER_TURBO = "whisper-turbo"


class TranscriptionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TranscriptionSegment:
    start_time: float  # in seconds
    end_time: float  # in seconds
    text: str
    confidence: float


@dataclass
class Transcription:
    id: str
    audio_file_id: str
    user_id: int
    model: TranscriptionModel
    status: TranscriptionStatus
    language: Optional[str] = None
    segments: List[TranscriptionSegment] = None
    error_message: Optional[str] = None