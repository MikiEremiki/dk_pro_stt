import asyncio
import logging
import structlog

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.types import BotCommand, BotCommandScopeChat
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_dialog import setup_dialogs

from src.application.bot.middlewares import register_middlewares
from src.config.settings import config
from src.application.bot.handlers import register_handlers
from src.application.bot.dialogs import register_dialogs

# Настройка логирования
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()


async def setup_bot_commands(bot: Bot):
    """Setup bot commands."""
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="Show help"),
        BotCommand(command="settings", description="Bot settings"),
    ]
    await bot.delete_my_commands(BotCommandScopeChat(chat_id=454342281))
    await bot.set_my_commands(commands)
    await bot.send_message(chat_id=454342281, text="Bot commands are set up")


async def main():
    """Start the Telegram bot."""
    logger.info("Bot started")

    # Настройка хранилища состояний
    key_builder = DefaultKeyBuilder(
        with_destiny=True  # Include destiny in the key
    )
    storage = RedisStorage.from_url(config.REDIS_URL, key_builder=key_builder)

    # Создание экземпляра бота и диспетчера
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=storage)

    # Регистрация обработчиков
    register_handlers(dp)

    register_middlewares(dp)

    # Регистрация диалогов
    register_dialogs(dp)
    setup_dialogs(dp)

    # Setup commands
    await setup_bot_commands(bot)

    # Start polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
