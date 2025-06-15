import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type, Union

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logger = logging.getLogger(__name__)


class BaseDialog(ABC):
    """Base class for all dialogs."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.router = Router()
        self.setup_handlers()

    @abstractmethod
    def setup_handlers(self) -> None:
        """Setup message and callback handlers."""
        pass

    def register_router(self, dp: Dispatcher) -> None:
        """Register the dialog's router with the dispatcher."""
        dp.include_router(self.router)
        logger.info(f"Registered router for {self.__class__.__name__}")


class BaseStates(StatesGroup):
    """Base states for dialogs."""
    START = State()
    WAITING_FOR_AUDIO = State()
    PROCESSING_AUDIO = State()
    WAITING_FOR_TRANSCRIPTION_PARAMS = State()
    PROCESSING_TRANSCRIPTION = State()
    WAITING_FOR_DIARIZATION_PARAMS = State()
    PROCESSING_DIARIZATION = State()
    WAITING_FOR_EXPORT_PARAMS = State()
    PROCESSING_EXPORT = State()
    COMPLETED = State()
    ERROR = State()


class MainDialog(BaseDialog):
    """Main dialog for the bot."""

    def setup_handlers(self) -> None:
        """Setup message and callback handlers."""
        self.router.message.register(self.start_handler, Command("start"))
        self.router.message.register(self.help_handler, Command("help"))
        self.router.message.register(self.settings_handler, Command("settings"))
        self.router.message.register(self.audio_handler, lambda msg: msg.audio is not None or msg.voice is not None)

    async def start_handler(self, message: Message, state: FSMContext) -> None:
        """Handle /start command."""
        await state.set_state(BaseStates.START)
        await message.answer(
            "👋 Welcome to the Audio Transcription Bot!\n\n"
            "I can transcribe audio files and identify different speakers.\n\n"
            "Send me an audio file to get started, or use /help to see available commands."
        )

    async def help_handler(self, message: Message) -> None:
        """Handle /help command."""
        await message.answer(
            "🔍 Help:\n\n"
            "- Send an audio file to transcribe it\n"
            "- /settings - Configure your preferences\n"
            "- /help - Show this help message\n\n"
            "Supported audio formats: MP3, WAV, OGG, M4A, WEBM"
        )

    async def settings_handler(self, message: Message, state: FSMContext) -> None:
        """Handle /settings command."""
        # This would be implemented in a separate dialog
        await message.answer("⚙️ Settings dialog would be shown here")

    async def audio_handler(self, message: Message, state: FSMContext) -> None:
        """Handle audio file messages."""
        await state.set_state(BaseStates.WAITING_FOR_AUDIO)
        
        file_id = None
        if message.audio:
            file_id = message.audio.file_id
            file_name = message.audio.file_name
            file_size = message.audio.file_size
            duration = message.audio.duration
        elif message.voice:
            file_id = message.voice.file_id
            file_name = f"voice_{file_id}.ogg"
            file_size = message.voice.file_size
            duration = message.voice.duration
        
        if not file_id:
            await message.answer("❌ Could not process the audio file. Please try again.")
            await state.set_state(BaseStates.ERROR)
            return
        
        await message.answer(
            f"🎵 Received audio file: {file_name}\n"
            f"Size: {file_size // 1024} KB\n"
            f"Duration: {duration} seconds\n\n"
            "Processing... This may take a while."
        )
        
        # Here we would call the application service to process the audio
        # For now, we'll just simulate a successful processing
        await state.set_state(BaseStates.PROCESSING_AUDIO)
        await message.answer("✅ Audio file processed successfully. Starting transcription...")
        
        # Simulate transcription
        await state.set_state(BaseStates.PROCESSING_TRANSCRIPTION)
        await message.answer("✅ Transcription completed successfully.")
        
        # Final message
        await state.set_state(BaseStates.COMPLETED)
        await message.answer(
            "🎉 All done! Here's a sample transcription:\n\n"
            "Speaker 1: Hello, this is a test.\n"
            "Speaker 2: Yes, I can hear you clearly.\n"
            "Speaker 1: Great, let's proceed with the meeting."
        )