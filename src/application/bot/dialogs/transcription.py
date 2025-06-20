import asyncio

from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format

from src.domains.audio.services import AudioService
from src.domains.transcription.services import TranscriptionService
from src.domains.diarization.services import DiarizationService


# Состояния диалога
class TranscriptionDialog(StatesGroup):
    transcription = State()
    processing = State()
    result = State()
    export = State()


# Обработчики
async def start_transcription(start_data, result, dialog_manager: DialogManager):
    """Start transcription process."""
    # Получение данных из контекста
    file_id = dialog_manager.start_data.get("file_id")
    file_name = dialog_manager.start_data.get("file_name")
    user_id = dialog_manager.start_data.get("user_id")
    
    # Сохранение данных в контексте диалога
    dialog_manager.dialog_data.update({
        "file_id": file_id,
        "file_name": file_name,
        "user_id": user_id,
        "status": "processing",
        "progress": 0,
    })
    
    # Переход к окну обработки
    await dialog_manager.switch_to(TranscriptionDialog.processing)


async def get_processing_data(dialog_manager: DialogManager, **kwargs):
    """Get processing data for the dialog."""
    return {
        "file_name": dialog_manager.dialog_data.get("file_name"),
        "status": dialog_manager.dialog_data.get("status"),
        "progress": dialog_manager.dialog_data.get("progress", 0),
    }


async def process_file(
    dialog_manager: DialogManager,
    audio_service: AudioService,
    transcription_service: TranscriptionService,
    diarization_service: DiarizationService,
    **kwargs
):
    """Process the file in background."""
    # В реальном приложении здесь будет отправка задачи в очередь
    # и периодическое обновление прогресса
    
    # Имитация прогресса обработки
    for progress in range(0, 101, 10):
        dialog_manager.dialog_data["progress"] = progress
        await dialog_manager.update({"progress": progress})
        await asyncio.sleep(1)  # Имитация задержки
    
    # Переход к результатам
    dialog_manager.dialog_data["status"] = "completed"
    await dialog_manager.switch_to(TranscriptionDialog.result)


async def get_result_data(dialog_manager: DialogManager, **kwargs):
    """Get result data for the dialog."""
    # В реальном приложении здесь будет получение результатов из базы данных
    return {
        "file_name": dialog_manager.dialog_data.get("file_name"),
        "transcription_id": "sample-id",  # Заглушка
        "duration": 120,  # Заглушка, секунды
        "language": "ru",  # Заглушка
        "speakers": 2,  # Заглушка
    }


async def on_export_click(
    callback: CallbackQuery, 
    button: Button, 
    dialog_manager: DialogManager,
):
    """Handle export button click."""
    # Переход к окну экспорта
    await dialog_manager.switch_to(TranscriptionDialog.export)


# Окна диалога
processing_window = Window(
    Const("⏳ Обработка аудио"),
    Format("Файл: {file_name}"),
    Format("Статус: {status}"),
    Format("Прогресс: {progress}%"),
    state=TranscriptionDialog.processing,
    getter=get_processing_data
)

result_window = Window(
    Const("✅ Транскрипция завершена"),
    Format("Файл: {file_name}"),
    Format("Длительность: {duration} сек."),
    Format("Язык: {language}"),
    Format("Количество спикеров: {speakers}"),
    Button(
        Const("📤 Экспорт"),
        id="export",
        on_click=on_export_click
    ),
    Button(
        Const("🔄 Новая транскрипция"),
        id="new",
        on_click=lambda c, b, m: m.done()
    ),
    state=TranscriptionDialog.result,
    getter=get_result_data
)

export_window = Window(
    Const("📤 Выберите формат экспорта"),
    Button(
        Const("📝 DOCX"),
        id="docx",
        on_click=lambda c, b, m: None  # Здесь будет обработчик экспорта
    ),
    Button(
        Const("🎬 SRT"),
        id="srt",
        on_click=lambda c, b, m: None  # Здесь будет обработчик экспорта
    ),
    Button(
        Const("🔢 JSON"),
        id="json",
        on_click=lambda c, b, m: None  # Здесь будет обработчик экспорта
    ),
    Button(
        Const("📄 TXT"),
        id="txt",
        on_click=lambda c, b, m: None  # Здесь будет обработчик экспорта
    ),
    Button(
        Const("◀️ Назад"),
        id="back",
        on_click=lambda c, b, m: m.switch_to(TranscriptionDialog.result)
    ),
    state=TranscriptionDialog.export
)

# Создание диалога
transcription_dialog = Dialog(
    Window(
        Const("🎵 Транскрипция аудио"),
        Const("Начинаю обработку файла..."),
        state=TranscriptionDialog.transcription,
        on_process_result=start_transcription
    ),
    processing_window,
    result_window,
    export_window
)