from typing import Optional


class AudioDomainError(Exception):
    """Base exception for Audio domain."""
    pass


class AudioValidationError(AudioDomainError):
    """Raised when audio file validation fails."""
    def __init__(self, message: str, file_id: Optional[str] = None):
        self.file_id = file_id
        super().__init__(message)


class AudioConversionError(AudioDomainError):
    """Raised when audio file conversion fails."""
    def __init__(self, message: str, file_id: Optional[str] = None, source_format: Optional[str] = None):
        self.file_id = file_id
        self.source_format = source_format
        super().__init__(message)


class AudioProcessingError(AudioDomainError):
    """Raised when audio processing (normalization, silence detection, etc.) fails."""
    def __init__(self, message: str, file_id: Optional[str] = None, operation: Optional[str] = None):
        self.file_id = file_id
        self.operation = operation
        super().__init__(message)