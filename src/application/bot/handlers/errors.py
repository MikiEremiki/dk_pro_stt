import structlog
from aiogram import Dispatcher
from aiogram.types import ErrorEvent
from aiogram.exceptions import TelegramAPIError


logger = structlog.get_logger()


async def handle_errors(error: ErrorEvent, bot):
    """Handle errors in update processing."""
    # Получение информации об ошибке
    exception = error.exception
    
    # Логирование ошибки
    logger.error(
        "Error while processing update",
        exception=str(exception),
        update=error.update.model_dump() if error.update else None,
    )
    
    # Обработка различных типов ошибок
    if isinstance(exception, TelegramAPIError):
        # Ошибки API Telegram
        logger.error("Telegram API error", code=error.status_code)
    else:
        # Другие ошибки
        logger.exception("Unhandled exception")
    
    # Отправка сообщения пользователю, если возможно
    if error.update and hasattr(error.update, "message"):
        try:
            await bot.send_message(
                error.update.message.chat.id,
                "⚠️ Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже."
            )
        except Exception as e:
            logger.error("Failed to send error message to user", exception=str(e))


def register_error_handlers(dp: Dispatcher):
    """Register error handlers."""
    dp.errors.register(handle_errors)