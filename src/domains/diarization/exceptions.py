from typing import Optional


class DiarizationDomainError(Exception):
    """Base exception for Diarization domain."""
    pass


class DiarizationTaskCreationError(DiarizationDomainError):
    """Raised when diarization task creation fails."""
    def __init__(self, message: str, audio_file_id: Optional[str] = None, user_id: Optional[int] = None):
        self.audio_file_id = audio_file_id
        self.user_id = user_id
        super().__init__(message)


class DiarizationProcessingError(DiarizationDomainError):
    """Raised when diarization processing fails."""
    def __init__(self, message: str, diarization_id: Optional[str] = None):
        self.diarization_id = diarization_id
        super().__init__(message)


class SpeakerEstimationError(DiarizationDomainError):
    """Raised when speaker estimation fails."""
    def __init__(self, message: str, audio_path: Optional[str] = None):
        self.audio_path = audio_path
        super().__init__(message)


class MergeWithTranscriptionError(DiarizationDomainError):
    """Raised when merging diarization with transcription fails."""
    def __init__(self, message: str, diarization_id: Optional[str] = None, transcription_id: Optional[str] = None):
        self.diarization_id = diarization_id
        self.transcription_id = transcription_id
        super().__init__(message)