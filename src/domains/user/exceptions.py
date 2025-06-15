from typing import Optional


class UserDomainError(Exception):
    """Base exception for User domain."""
    pass


class UserNotFoundError(UserDomainError):
    """Raised when a user is not found."""
    def __init__(self, message: str, user_id: Optional[int] = None, username: Optional[str] = None):
        self.user_id = user_id
        self.username = username
        super().__init__(message)


class UserCreationError(UserDomainError):
    """Raised when user creation fails."""
    def __init__(self, message: str, user_id: Optional[int] = None, username: Optional[str] = None):
        self.user_id = user_id
        self.username = username
        super().__init__(message)


class UserUpdateError(UserDomainError):
    """Raised when user update fails."""
    def __init__(self, message: str, user_id: Optional[int] = None):
        self.user_id = user_id
        super().__init__(message)


class UserSettingsNotFoundError(UserDomainError):
    """Raised when user settings are not found."""
    def __init__(self, message: str, user_id: Optional[int] = None):
        self.user_id = user_id
        super().__init__(message)


class UserSettingsUpdateError(UserDomainError):
    """Raised when user settings update fails."""
    def __init__(self, message: str, user_id: Optional[int] = None):
        self.user_id = user_id
        super().__init__(message)