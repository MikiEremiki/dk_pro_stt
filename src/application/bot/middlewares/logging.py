import structlog
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

logger = structlog.get_logger()


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging all updates."""

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        # Получение информации о пользователе
        user = data.get("event_from_user", None)
        if user and isinstance(user, User):
            user_info = {
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        else:
            user_info = {"user_id": "unknown"}

        # Логирование события
        logger.info(
            "Received update",
            update_type=event.__class__.__name__,
            **user_info
        )
        print(event)

        # Вызов следующего обработчика
        return await handler(event, data)