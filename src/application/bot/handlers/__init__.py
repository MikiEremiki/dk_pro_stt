from aiogram import Dispatcher

from .commands import register_command_handlers
from .audio import register_audio_handlers
from .voice import register_voice_handlers
from .errors import register_error_handlers


def register_handlers(dp: Dispatcher):
    """Register all handlers."""
    register_command_handlers(dp)
    register_audio_handlers(dp)
    register_voice_handlers(dp)
    register_error_handlers(dp)