import structlog
from aiogram import Dispatcher, F
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from src.application.bot.dialogs.transcription import TranscriptionDialog
from src.domains.audio.services import AudioService


logger = structlog.get_logger()


async def handle_audio(
    message: Message, 
    dialog_manager: DialogManager, 
    audio_service: AudioService
):
    """Handle audio files."""
    # Получение информации о файле
    file_id = message.audio.file_id
    file_name = message.audio.file_name or f"audio_{file_id}.mp3"
    file_size = message.audio.file_size
    
    # Проверка размера файла
    if file_size > 200 * 1024 * 1024:  # 200 MB
        await message.answer(
            "⚠️ Файл слишком большой. Максимальный размер - 200 MB."
        )
        return
    
    # Отправка сообщения о начале обработки
    await message.answer(
        f"🎵 Получен аудиофайл: {file_name}\n"
        f"📊 Размер: {file_size / 1024 / 1024:.2f} MB\n\n"
        "⏳ Начинаю обработку..."
    )
    
    # Запуск диалога транскрипции
    await dialog_manager.start(
        TranscriptionDialog.transcription,
        data={"file_id": file_id, "file_name": file_name, "user_id": message.from_user.id},
        mode=StartMode.RESET_STACK
    )


def register_audio_handlers(dp: Dispatcher):
    """Register audio handlers."""
    dp.message.register(handle_audio, F.audio)