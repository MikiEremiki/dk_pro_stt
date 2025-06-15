from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


class ExportFormat(str, Enum):
    DOCX = "docx"
    TXT = "txt"
    SRT = "srt"
    VTT = "vtt"
    JSON = "json"


class TranscriptionModel(str, Enum):
    WHISPER_LARGE_V3 = "whisper-large-v3"
    WHISPER_TURBO = "whisper-turbo"


@dataclass
class User:
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class UserSettings:
    user_id: int
    preferred_model: TranscriptionModel = TranscriptionModel.WHISPER_LARGE_V3
    preferred_export_format: ExportFormat = ExportFormat.DOCX
    auto_detect_language: bool = True
    auto_delete_files: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None