import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from src.config.settings import config

logger = logging.getLogger(__name__)


async def setup_bot_commands(bot: Bot):
    """Setup bot commands."""
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="Show help"),
    ]
    await bot.set_my_commands(commands)
    await bot.send_message(chat_id=454342281, text="Bot commands are set up")


async def main():
    """Start the Telegram bot."""
    logger.info("Bot started")

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    # Setup commands
    await setup_bot_commands(bot)

    # Start polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
