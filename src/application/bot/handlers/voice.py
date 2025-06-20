import structlog
from aiogram import Dispatcher, F
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from src.application.bot.dialogs.transcription import TranscriptionDialog
from src.domains.audio.services import AudioService


logger = structlog.get_logger()


async def handle_voice(
    message: Message, 
    dialog_manager: DialogManager, 
):
    """Handle voice messages."""
    # Получение информации о файле
    file_id = message.voice.file_id
    file_name = f"voice_{file_id}.ogg"
    file_size = message.voice.file_size
    
    # Проверка размера файла
    if file_size > 200 * 1024 * 1024:  # 200 MB
        await message.answer(
            "⚠️ Файл слишком большой. Максимальный размер - 200 MB."
        )
        return
    
    # Отправка сообщения о начале обработки
    await message.answer(
        f"🎤 Получено голосовое сообщение\n"
        f"📊 Размер: {file_size / 1024 / 1024:.2f} MB\n\n"
        "⏳ Начинаю обработку..."
    )

    user_id = message.from_user.id
    dialog_manager.dialog_data.update({
        "file_id": file_id,
        "file_name": file_name,
        "user_id": user_id,
        "status": "processing",
        "progress": 0,
    })
    # Запуск диалога транскрипции
    await dialog_manager.start(
        TranscriptionDialog.result,
        data={"file_id": file_id, "file_name": file_name, "user_id": user_id},
        mode=StartMode.RESET_STACK
    )


def register_voice_handlers(dp: Dispatcher):
    """Register voice handlers."""
    dp.message.register(handle_voice, F.voice)