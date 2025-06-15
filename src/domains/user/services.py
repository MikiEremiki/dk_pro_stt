from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from .entities import User, UserSettings, TranscriptionModel, ExportFormat


class UserService(ABC):
    @abstractmethod
    async def create_user(self, user_id: int, username: Optional[str] = None, **user_data) -> User:
        """Create a new user"""
        pass

    @abstractmethod
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        pass

    @abstractmethod
    async def update_user(self, user_id: int, **user_data) -> User:
        """Update user data"""
        pass

    @abstractmethod
    async def delete_user(self, user_id: int) -> None:
        """Delete user"""
        pass


class UserSettingsService(ABC):
    @abstractmethod
    async def get_user_settings(self, user_id: int) -> UserSettings:
        """Get user settings, creating default settings if they don't exist"""
        pass

    @abstractmethod
    async def update_user_settings(
        self,
        user_id: int,
        preferred_model: Optional[TranscriptionModel] = None,
        preferred_export_format: Optional[ExportFormat] = None,
        auto_detect_language: Optional[bool] = None,
        auto_delete_files: Optional[bool] = None,
    ) -> UserSettings:
        """Update user settings"""
        pass

    @abstractmethod
    async def reset_user_settings(self, user_id: int) -> UserSettings:
        """Reset user settings to defaults"""
        pass

    @abstractmethod
    async def get_settings_as_dict(self, user_id: int) -> Dict[str, Any]:
        """Get user settings as a dictionary for easy access in application layer"""
        pass