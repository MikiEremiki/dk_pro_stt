from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from src.application.bot.dialogs.settings import SettingsDialog
from src.application.bot.dialogs.help import HelpDialog


async def cmd_start(message: Message, dialog_manager: DialogManager):
    """Handle /start command."""
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я бот для транскрипции аудио с диаризацией спикеров. "
        "Отправь мне голосовое сообщение или аудиофайл, и я преобразую его в текст.\n\n"
        "Используй /help для получения справки."
    )



async def cmd_help(message: Message, dialog_manager: DialogManager):
    """Handle /help command."""
    await dialog_manager.start(HelpDialog.help, mode=StartMode.RESET_STACK)


async def cmd_settings(message: Message, dialog_manager: DialogManager):
    """Handle /settings command."""
    await dialog_manager.start(SettingsDialog.settings, mode=StartMode.RESET_STACK)


def register_command_handlers(dp: Dispatcher):
    """Register command handlers."""
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_settings, Command("settings"))