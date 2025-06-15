from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class ExportFormat(str, Enum):
    DOCX = "docx"
    TXT = "txt"
    SRT = "srt"
    VTT = "vtt"
    JSON = "json"


class ExportStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Export:
    id: str
    user_id: int
    transcription_id: Optional[str] = None
    diarization_id: Optional[str] = None
    format: ExportFormat = ExportFormat.DOCX
    status: ExportStatus = ExportStatus.PENDING
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None