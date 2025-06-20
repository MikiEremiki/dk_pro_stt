from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime

from .entities import User, UserSettings, TranscriptionModel, ExportFormat
from .repositories import UserSettingsRepository


class UserService():
    async def create_user(self, user_id: int, username: Optional[str] = None, **user_data) -> User:
        """Create a new user"""
        pass

    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        pass

    async def update_user(self, user_id: int, **user_data) -> User:
        """Update user data"""
        pass

    async def delete_user(self, user_id: int) -> None:
        """Delete user"""
        pass


class UserSettingsService:
    def __init__(self, settings_repository: UserSettingsRepository):
        self.settings_repository = settings_repository

    async def get_user_settings(self, user_id: int) -> UserSettings:
        """Get user settings, creating default settings if they don't exist"""
        settings = await self.settings_repository.get_by_user_id(user_id)

        if settings is None:
            # Create default settings
            now = datetime.now()
            settings = UserSettings(
                user_id=user_id,
                created_at=now,
                updated_at=now
            )
            # Save the default settings
            settings = await self.settings_repository.save(settings)

        return settings

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

    async def reset_user_settings(self, user_id: int) -> UserSettings:
        """Reset user settings to defaults"""
        pass

    async def get_settings_as_dict(self, user_id: int) -> Dict[str, Any]:
        """Get user settings as a dictionary for easy access in application layer"""
        pass
