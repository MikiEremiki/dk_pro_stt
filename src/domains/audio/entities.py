from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class AudioFormat(str, Enum):
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    M4A = "m4a"
    WEBM = "webm"


@dataclass
class AudioFile:
    id: str
    user_id: int
    original_filename: str
    format: AudioFormat
    size_bytes: int
    duration_seconds: Optional[float] = None
    path: Optional[Path] = None
    processed_path: Optional[Path] = None
    is_valid: bool = False
    error_message: Optional[str] = None