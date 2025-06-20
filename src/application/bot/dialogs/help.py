from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const


# Состояния диалога
from aiogram.fsm.state import StatesGroup, State


class HelpDialog(StatesGroup):
    help = State()


# Обработчики
async def get_help_data(dialog_manager: DialogManager, **kwargs):
    """Get help data."""
    return {}


# Окна диалога
help_window = Window(
    Const("📚 Справка"),
    Const(
        "Этот бот предназначен для транскрипции аудио с диаризацией спикеров.\n\n"
        "Основные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n"
        "/settings - Настройки бота\n\n"
        "Как использовать бот:\n"
        "1. Отправьте аудиофайл или голосовое сообщение\n"
        "2. Дождитесь завершения обработки\n"
        "3. Получите результат транскрипции\n"
        "4. При необходимости выберите формат экспорта\n\n"
        "Поддерживаемые форматы аудио:\n"
        "- MP3, OGG, WAV, M4A и другие популярные форматы\n"
        "- Голосовые сообщения Telegram\n\n"
        "Максимальный размер файла: 200 MB"
    ),
    Button(
        Const("✅ Понятно"),
        id="done",
        on_click=lambda c, b, m: m.done()
    ),
    state=HelpDialog.help,
    getter=get_help_data
)

# Создание диалога
help_dialog = Dialog(help_window)