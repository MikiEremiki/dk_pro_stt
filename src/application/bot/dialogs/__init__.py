from aiogram import Dispatcher

from .settings import settings_dialog
from .help import help_dialog
from .transcription import transcription_dialog


def register_dialogs(dp: Dispatcher):
    """Register all dialogs."""
    dp.include_routers(
        settings_dialog,
        help_dialog,
        transcription_dialog
    )
