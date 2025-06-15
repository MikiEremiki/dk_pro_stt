from abc import ABC, abstractmethod
from typing import Optional, List

from .entities import User, UserSettings


class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> None:
        pass


class UserSettingsRepository(ABC):
    @abstractmethod
    async def save(self, settings: UserSettings) -> UserSettings:
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> Optional[UserSettings]:
        pass

    @abstractmethod
    async def update(self, settings: UserSettings) -> UserSettings:
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> None:
        pass