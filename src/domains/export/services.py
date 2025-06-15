from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, BinaryIO

from .entities import Export, ExportFormat


class ExportService(ABC):
    @abstractmethod
    async def create_export_task(
        self,
        user_id: int,
        format: ExportFormat,
        transcription_id: Optional[str] = None,
        diarization_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Export:
        """Create a new export task"""
        pass

    @abstractmethod
    async def process_export(self, export_id: str) -> Export:
        """Process export task"""
        pass

    @abstractmethod
    async def get_export(self, export_id: str) -> Optional[Export]:
        """Get export by ID"""
        pass

    @abstractmethod
    async def get_export_file(self, export_id: str) -> BinaryIO:
        """Get export file content"""
        pass

    @abstractmethod
    async def generate_docx(
        self, transcription_id: str, diarization_id: Optional[str] = None, options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate DOCX file from transcription and optional diarization"""
        pass

    @abstractmethod
    async def generate_txt(
        self, transcription_id: str, diarization_id: Optional[str] = None, options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate TXT file from transcription and optional diarization"""
        pass

    @abstractmethod
    async def generate_srt(
        self, transcription_id: str, options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate SRT subtitle file from transcription"""
        pass

    @abstractmethod
    async def generate_vtt(
        self, transcription_id: str, options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate VTT subtitle file from transcription"""
        pass

    @abstractmethod
    async def generate_json(
        self, transcription_id: str, diarization_id: Optional[str] = None, options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate JSON file with transcription and optional diarization data"""
        pass