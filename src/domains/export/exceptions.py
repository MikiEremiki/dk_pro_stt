from typing import Optional

from .entities import ExportFormat


class ExportDomainError(Exception):
    """Base exception for Export domain."""
    pass


class ExportTaskCreationError(ExportDomainError):
    """Raised when export task creation fails."""
    def __init__(
        self,
        message: str,
        user_id: Optional[int] = None,
        transcription_id: Optional[str] = None,
        diarization_id: Optional[str] = None,
    ):
        self.user_id = user_id
        self.transcription_id = transcription_id
        self.diarization_id = diarization_id
        super().__init__(message)


class ExportProcessingError(ExportDomainError):
    """Raised when export processing fails."""
    def __init__(self, message: str, export_id: Optional[str] = None, format: Optional[ExportFormat] = None):
        self.export_id = export_id
        self.format = format
        super().__init__(message)


class ExportFileNotFoundError(ExportDomainError):
    """Raised when export file is not found."""
    def __init__(self, message: str, export_id: Optional[str] = None):
        self.export_id = export_id
        super().__init__(message)


class ExportFormatGenerationError(ExportDomainError):
    """Raised when generating a specific export format fails."""
    def __init__(
        self,
        message: str,
        format: Optional[ExportFormat] = None,
        transcription_id: Optional[str] = None,
        diarization_id: Optional[str] = None,
    ):
        self.format = format
        self.transcription_id = transcription_id
        self.diarization_id = diarization_id
        super().__init__(message)