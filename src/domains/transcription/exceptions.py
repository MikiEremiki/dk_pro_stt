from typing import Optional


class TranscriptionDomainError(Exception):
    """Base exception for Transcription domain."""
    pass


class TranscriptionTaskCreationError(TranscriptionDomainError):
    """Raised when transcription task creation fails."""
    def __init__(self, message: str, audio_file_id: Optional[str] = None, user_id: Optional[int] = None):
        self.audio_file_id = audio_file_id
        self.user_id = user_id
        super().__init__(message)


class TranscriptionProcessingError(TranscriptionDomainError):
    """Raised when transcription processing fails."""
    def __init__(self, message: str, transcription_id: Optional[str] = None):
        self.transcription_id = transcription_id
        super().__init__(message)


class LanguageDetectionError(TranscriptionDomainError):
    """Raised when language detection fails."""
    def __init__(self, message: str, audio_path: Optional[str] = None):
        self.audio_path = audio_path
        super().__init__(message)