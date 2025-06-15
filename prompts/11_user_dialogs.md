# Фаза 3, День 11: Диалоги пользователя: Прогресс-бары, настройки, история

## Цель (Definition of Done)
- Реализованы интерактивные диалоги с пользователем с использованием aiogram-dialog
- Добавлены прогресс-бары для отображения статуса обработки аудио
- Реализованы пользовательские настройки (качество/скорость транскрипции, язык и т.д.)
- Создана система хранения и отображения истории обработанных файлов
- Разработан интуитивно понятный интерфейс для навигации между функциями

## Ссылки на документацию
- [aiogram 3.x Documentation](https://docs.aiogram.dev/en/latest/)
- [aiogram-dialog Documentation](https://github.com/Tishka17/aiogram_dialog)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/)

---

## 1. Техническая секция

### Описание
В этом разделе мы реализуем пользовательский интерфейс бота с использованием aiogram-dialog, который обеспечит удобное взаимодействие пользователя с функциями транскрипции. Основные компоненты включают:

1. **Диалоговая система**: Структурированные диалоги для навигации по функциям бота
2. **Прогресс-бары**: Визуальное отображение прогресса обработки аудио
3. **Пользовательские настройки**: Персонализация параметров транскрипции
4. **История обработки**: Хранение и доступ к ранее обработанным файлам
5. **Уведомления**: Информирование пользователя о статусе задач

### Примеры кода

#### Структура диалогов

```python
# src/bot/dialogs/registry.py
from aiogram_dialog import DialogRegistry
from aiogram.dispatcher.router import Router

from src.bot.dialogs.main_menu import main_menu_dialog
from src.bot.dialogs.transcription import transcription_dialog
from src.bot.dialogs.settings import settings_dialog
from src.bot.dialogs.history import history_dialog
from src.bot.dialogs.progress import progress_dialog

def setup_dialogs(router: Router) -> DialogRegistry:
    """Register all dialogs in the registry."""
    registry = DialogRegistry(router)
    
    # Register dialogs
    registry.register(main_menu_dialog)
    registry.register(transcription_dialog)
    registry.register(settings_dialog)
    registry.register(history_dialog)
    registry.register(progress_dialog)
    
    return registry
```

#### Главное меню

```python
# src/bot/dialogs/main_menu.py
from typing import Any, Dict

from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, Select, Cancel
from aiogram_dialog.widgets.text import Const, Format

from src.bot.states import MainMenuState, TranscriptionState, SettingsState, HistoryState

async def start_handler(message: Message, dialog_manager: DialogManager):
    """Handler for /start command."""
    await dialog_manager.start(MainMenuState.main)

async def on_transcribe_selected(callback: CallbackQuery, button: Button, 
                                dialog_manager: DialogManager):
    """Handler for transcription button."""
    await dialog_manager.start(TranscriptionState.upload)

async def on_settings_selected(callback: CallbackQuery, button: Button, 
                              dialog_manager: DialogManager):
    """Handler for settings button."""
    await dialog_manager.start(SettingsState.main)

async def on_history_selected(callback: CallbackQuery, button: Button, 
                             dialog_manager: DialogManager):
    """Handler for history button."""
    await dialog_manager.start(HistoryState.list)

# Main menu window
main_menu_window = Window(
    Const("🎙 Добро пожаловать в Transcription Bot!\n\nВыберите действие:"),
    Row(
        Button(
            Const("🔊 Транскрибировать аудио"),
            id="transcribe",
            on_click=on_transcribe_selected
        ),
    ),
    Row(
        Button(
            Const("⚙️ Настройки"),
            id="settings",
            on_click=on_settings_selected
        ),
        Button(
            Const("📜 История"),
            id="history",
            on_click=on_history_selected
        ),
    ),
    state=MainMenuState.main
)

# Create dialog
main_menu_dialog = Dialog(main_menu_window)
```

#### Диалог транскрипции

```python
# src/bot/dialogs/transcription.py
from typing import Any, Dict

from aiogram import F
from aiogram.types import CallbackQuery, Message, ContentType
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, Select, Back, Cancel
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput

from src.bot.states import TranscriptionState, ProgressState
from src.domains.audio.services import AudioService
from src.domains.transcription.services import TranscriptionService
from src.domains.user.services import UserService

async def on_file_received(message: Message, dialog_manager: DialogManager, 
                          audio_service: AudioService):
    """Handler for receiving audio file."""
    # Get user settings
    user_id = message.from_user.id
    user_service = UserService()
    settings = await user_service.get_user_settings(user_id)
    
    # Process file
    file_id = message.audio.file_id if message.audio else message.voice.file_id
    file_info = await audio_service.validate_audio_file(file_id)
    
    if file_info:
        # Store file info in dialog data
        dialog_manager.dialog_data["file_id"] = file_id
        dialog_manager.dialog_data["file_name"] = file_info.get("file_name", "audio")
        dialog_manager.dialog_data["file_size"] = file_info.get("file_size", 0)
        dialog_manager.dialog_data["duration"] = file_info.get("duration", 0)
        
        # Go to confirmation window
        await dialog_manager.next()
    else:
        # Show error message
        await message.answer("❌ Файл не поддерживается или слишком большой. "
                           "Поддерживаемые форматы: mp3, wav, ogg, m4a. "
                           "Максимальный размер: 200MB.")

async def on_start_transcription(callback: CallbackQuery, button: Button, 
                                dialog_manager: DialogManager,
                                transcription_service: TranscriptionService):
    """Handler for starting transcription."""
    # Get file info from dialog data
    file_id = dialog_manager.dialog_data["file_id"]
    user_id = callback.from_user.id
    
    # Get user settings
    user_service = UserService()
    settings = await user_service.get_user_settings(user_id)
    
    # Create transcription task
    task_id = await transcription_service.create_transcription_task(
        file_id=file_id,
        user_id=user_id,
        model=settings.get("model", "whisper-large-v3"),
        language=settings.get("language", "auto"),
        diarization=settings.get("diarization", True)
    )
    
    # Store task_id in dialog data
    dialog_manager.dialog_data["task_id"] = task_id
    
    # Switch to progress dialog
    await dialog_manager.start(ProgressState.tracking, data={"task_id": task_id})

# Upload window
upload_window = Window(
    Const("📤 Отправьте аудио или голосовое сообщение для транскрипции."),
    Const("Поддерживаемые форматы: mp3, wav, ogg, m4a. Максимальный размер: 200MB."),
    MessageInput(on_file_received, content_types=[ContentType.AUDIO, ContentType.VOICE]),
    Row(
        Cancel(Const("🔙 Назад"))
    ),
    state=TranscriptionState.upload
)

# Confirmation window
confirmation_window = Window(
    Format("📋 Информация о файле:\n"
           "Название: {file_name}\n"
           "Размер: {file_size:.2f} MB\n"
           "Длительность: {duration:.1f} сек\n\n"
           "Начать транскрипцию?"),
    Row(
        Button(
            Const("✅ Начать"),
            id="start_transcription",
            on_click=on_start_transcription
        ),
        Back(Const("🔙 Назад"))
    ),
    getter=lambda dialog_manager, **kwargs: {
        "file_name": dialog_manager.dialog_data.get("file_name", "Неизвестно"),
        "file_size": dialog_manager.dialog_data.get("file_size", 0) / (1024 * 1024),  # Convert to MB
        "duration": dialog_manager.dialog_data.get("duration", 0)
    },
    state=TranscriptionState.confirm
)

# Create dialog
transcription_dialog = Dialog(upload_window, confirmation_window)
```

#### Прогресс-бар

```python
# src/bot/dialogs/progress.py
from typing import Any, Dict
import asyncio

from aiogram import F
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, Cancel
from aiogram_dialog.widgets.text import Const, Format

from src.bot.states import ProgressState, MainMenuState
from src.domains.transcription.services import TranscriptionService

async def progress_getter(dialog_manager: DialogManager, 
                         transcription_service: TranscriptionService, **kwargs):
    """Get progress information for the task."""
    task_id = dialog_manager.dialog_data.get("task_id")
    if not task_id:
        return {
            "progress": 0,
            "status": "Ошибка: задача не найдена",
            "progress_bar": "⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜",
            "is_completed": True,
            "is_failed": True
        }
    
    # Get task status
    task_status = await transcription_service.get_task_status(task_id)
    
    # Calculate progress bar
    progress = task_status.get("progress", 0)
    progress_blocks = int(progress * 10)
    progress_bar = "🟩" * progress_blocks + "⬜" * (10 - progress_blocks)
    
    # Check if task is completed or failed
    is_completed = task_status.get("status") == "completed"
    is_failed = task_status.get("status") == "failed"
    
    # If completed or failed, stop polling
    if is_completed or is_failed:
        dialog_manager.dialog_data["stop_polling"] = True
        
        # If completed, store result in dialog data
        if is_completed:
            dialog_manager.dialog_data["result"] = task_status.get("result")
    
    return {
        "progress": int(progress * 100),
        "status": task_status.get("status_message", "Обработка..."),
        "progress_bar": progress_bar,
        "is_completed": is_completed,
        "is_failed": is_failed,
        "error_message": task_status.get("error_message", "")
    }

async def on_process_complete(callback: CallbackQuery, button: Button, 
                             dialog_manager: DialogManager):
    """Handler for viewing results."""
    # Get result from dialog data
    result = dialog_manager.dialog_data.get("result")
    
    # Here you would typically show the result or redirect to a result view
    # For now, we'll just go back to the main menu
    await dialog_manager.start(MainMenuState.main)

async def on_process_cancel(callback: CallbackQuery, button: Button, 
                           dialog_manager: DialogManager,
                           transcription_service: TranscriptionService):
    """Handler for canceling the task."""
    task_id = dialog_manager.dialog_data.get("task_id")
    if task_id:
        await transcription_service.cancel_task(task_id)
    
    # Go back to main menu
    await dialog_manager.start(MainMenuState.main)

async def on_dialog_started(start_data: Dict[str, Any], manager: DialogManager):
    """Called when dialog is started."""
    # Store task_id in dialog data
    if start_data and "task_id" in start_data:
        manager.dialog_data["task_id"] = start_data["task_id"]
    
    # Start polling for progress updates
    manager.dialog_data["stop_polling"] = False
    asyncio.create_task(poll_progress(manager))

async def poll_progress(manager: DialogManager):
    """Poll for progress updates."""
    while not manager.dialog_data.get("stop_polling", False):
        await manager.update({})  # Trigger getter to update progress
        await asyncio.sleep(1)  # Poll every second

# Progress tracking window
progress_window = Window(
    Const("🔄 Обработка аудио..."),
    Format("{progress_bar} {progress}%"),
    Format("Статус: {status}"),
    Row(
        Button(
            Const("❌ Отменить"),
            id="cancel_process",
            on_click=on_process_cancel,
            when=lambda data, widget, manager: not data.get("is_completed") and not data.get("is_failed")
        ),
    ),
    Row(
        Button(
            Const("✅ Просмотреть результат"),
            id="view_result",
            on_click=on_process_complete,
            when=lambda data, widget, manager: data.get("is_completed")
        ),
    ),
    Row(
        Button(
            Const("🔙 Вернуться в меню"),
            id="back_to_menu",
            on_click=lambda c, b, m: m.start(MainMenuState.main),
            when=lambda data, widget, manager: data.get("is_failed")
        ),
    ),
    Format("❌ Ошибка: {error_message}", 
           when=lambda data, widget, manager: data.get("is_failed")),
    state=ProgressState.tracking,
    getter=progress_getter,
    on_start=on_dialog_started
)

# Create dialog
progress_dialog = Dialog(progress_window)
```

#### Настройки пользователя

```python
# src/bot/dialogs/settings.py
from typing import Any, Dict

from aiogram import F
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, Select, Cancel, Group, Radio, Checkbox
from aiogram_dialog.widgets.text import Const, Format

from src.bot.states import SettingsState
from src.domains.user.services import UserService

async def settings_getter(dialog_manager: DialogManager, user_service: UserService, **kwargs):
    """Get user settings."""
    user_id = dialog_manager.event.from_user.id
    settings = await user_service.get_user_settings(user_id)
    
    return {
        "model": settings.get("model", "whisper-large-v3"),
        "language": settings.get("language", "auto"),
        "diarization": settings.get("diarization", True),
        "export_format": settings.get("export_format", "all")
    }

async def on_model_changed(callback: CallbackQuery, widget: Any, 
                          dialog_manager: DialogManager, item_id: str):
    """Handler for model selection."""
    user_id = callback.from_user.id
    user_service = UserService()
    await user_service.update_user_settings(user_id, {"model": item_id})
    await dialog_manager.update({})

async def on_language_changed(callback: CallbackQuery, widget: Any, 
                             dialog_manager: DialogManager, item_id: str):
    """Handler for language selection."""
    user_id = callback.from_user.id
    user_service = UserService()
    await user_service.update_user_settings(user_id, {"language": item_id})
    await dialog_manager.update({})

async def on_diarization_changed(callback: CallbackQuery, widget: Any, 
                               dialog_manager: DialogManager):
    """Handler for diarization toggle."""
    user_id = callback.from_user.id
    user_service = UserService()
    current_settings = await user_service.get_user_settings(user_id)
    current_diarization = current_settings.get("diarization", True)
    
    # Toggle diarization
    await user_service.update_user_settings(user_id, {"diarization": not current_diarization})
    await dialog_manager.update({})

async def on_export_format_changed(callback: CallbackQuery, widget: Any, 
                                 dialog_manager: DialogManager, item_id: str):
    """Handler for export format selection."""
    user_id = callback.from_user.id
    user_service = UserService()
    await user_service.update_user_settings(user_id, {"export_format": item_id})
    await dialog_manager.update({})

# Settings window
settings_window = Window(
    Const("⚙️ Настройки транскрипции"),
    Const("\n🤖 Модель:"),
    Radio(
        Format("✓ {item[0]}") if F.data["model"] == F.item[1] else Format("{item[0]}"),
        id="model_select",
        item_id_getter=lambda item: item[1],
        items=[
            ("Whisper Large (высокое качество)", "whisper-large-v3"),
            ("Whisper Turbo (быстрая обработка)", "whisper-turbo"),
        ],
        on_click=on_model_changed
    ),
    Const("\n🌐 Язык:"),
    Radio(
        Format("✓ {item[0]}") if F.data["language"] == F.item[1] else Format("{item[0]}"),
        id="language_select",
        item_id_getter=lambda item: item[1],
        items=[
            ("Автоопределение", "auto"),
            ("Русский", "ru"),
            ("Английский", "en"),
            ("Русский + Английский", "ru+en"),
        ],
        on_click=on_language_changed
    ),
    Const("\n👥 Диаризация (разделение по спикерам):"),
    Checkbox(
        Const("✅ Включена"),
        Const("❌ Выключена"),
        id="diarization_toggle",
        checked=F.data["diarization"],
        on_click=on_diarization_changed
    ),
    Const("\n📄 Формат экспорта:"),
    Radio(
        Format("✓ {item[0]}") if F.data["export_format"] == F.item[1] else Format("{item[0]}"),
        id="export_format_select",
        item_id_getter=lambda item: item[1],
        items=[
            ("Все форматы", "all"),
            ("Только текст", "text"),
            ("DOCX", "docx"),
            ("SRT", "srt"),
            ("JSON", "json"),
        ],
        on_click=on_export_format_changed
    ),
    Row(
        Cancel(Const("🔙 Назад"))
    ),
    state=SettingsState.main,
    getter=settings_getter
)

# Create dialog
settings_dialog = Dialog(settings_window)
```

#### История обработки

```python
# src/bot/dialogs/history.py
from typing import Any, Dict
from datetime import datetime

from aiogram import F
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, Select, Cancel, SwitchTo, Start
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.media import DynamicMedia

from src.bot.states import HistoryState, MainMenuState
from src.domains.user.services import UserService
from src.domains.transcription.services import TranscriptionService

async def history_list_getter(dialog_manager: DialogManager, 
                             user_service: UserService, **kwargs):
    """Get user's transcription history."""
    user_id = dialog_manager.event.from_user.id
    page = dialog_manager.dialog_data.get("page", 1)
    items_per_page = 5
    
    # Get history items with pagination
    history_items = await user_service.get_user_history(
        user_id, 
        page=page, 
        items_per_page=items_per_page
    )
    
    # Get total count for pagination
    total_count = await user_service.get_user_history_count(user_id)
    total_pages = (total_count + items_per_page - 1) // items_per_page
    
    # Format items for display
    formatted_items = []
    for item in history_items:
        # Format date
        created_at = item.get("created_at", datetime.now())
        date_str = created_at.strftime("%d.%m.%Y %H:%M")
        
        # Format duration
        duration = item.get("duration", 0)
        duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}"
        
        # Format status
        status = item.get("status", "unknown")
        status_emoji = "✅" if status == "completed" else "❌" if status == "failed" else "🔄"
        
        # Add to list
        formatted_items.append({
            "id": item.get("id"),
            "file_name": item.get("file_name", "Неизвестно"),
            "date": date_str,
            "duration": duration_str,
            "status": f"{status_emoji} {status.capitalize()}"
        })
    
    return {
        "history_items": formatted_items,
        "page": page,
        "total_pages": max(1, total_pages),
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "empty": len(formatted_items) == 0
    }

async def history_detail_getter(dialog_manager: DialogManager, 
                               transcription_service: TranscriptionService, **kwargs):
    """Get details for a specific history item."""
    item_id = dialog_manager.dialog_data.get("selected_item_id")
    if not item_id:
        return {"error": "Item not found"}
    
    # Get item details
    item = await transcription_service.get_task_details(item_id)
    if not item:
        return {"error": "Item not found"}
    
    # Format date
    created_at = item.get("created_at", datetime.now())
    date_str = created_at.strftime("%d.%m.%Y %H:%M")
    
    # Format duration
    duration = item.get("duration", 0)
    duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}"
    
    # Format status
    status = item.get("status", "unknown")
    status_emoji = "✅" if status == "completed" else "❌" if status == "failed" else "🔄"
    
    return {
        "id": item.get("id"),
        "file_name": item.get("file_name", "Неизвестно"),
        "date": date_str,
        "duration": duration_str,
        "status": f"{status_emoji} {status.capitalize()}",
        "model": item.get("model", "Неизвестно"),
        "language": item.get("language", "Неизвестно"),
        "diarization": "Включена" if item.get("diarization", False) else "Выключена",
        "speakers_count": item.get("speakers_count", 0),
        "error_message": item.get("error_message", ""),
        "is_completed": status == "completed",
        "is_failed": status == "failed"
    }

async def on_item_selected(callback: CallbackQuery, widget: Any, 
                          dialog_manager: DialogManager, item_id: str):
    """Handler for selecting a history item."""
    dialog_manager.dialog_data["selected_item_id"] = item_id
    await dialog_manager.switch_to(HistoryState.detail)

async def on_page_changed(callback: CallbackQuery, button: Button, 
                         dialog_manager: DialogManager, page_delta: int):
    """Handler for pagination."""
    current_page = dialog_manager.dialog_data.get("page", 1)
    new_page = max(1, current_page + page_delta)
    dialog_manager.dialog_data["page"] = new_page
    await dialog_manager.update({})

async def on_download_result(callback: CallbackQuery, button: Button, 
                            dialog_manager: DialogManager,
                            transcription_service: TranscriptionService):
    """Handler for downloading result."""
    item_id = dialog_manager.dialog_data.get("selected_item_id")
    if not item_id:
        return
    
    # Get download links
    download_links = await transcription_service.get_download_links(item_id)
    
    # Send links to user
    text = "📥 Скачать результаты:\n\n"
    if "text" in download_links:
        text += f"📝 [Текст]({download_links['text']})\n"
    if "docx" in download_links:
        text += f"📄 [DOCX]({download_links['docx']})\n"
    if "srt" in download_links:
        text += f"🎬 [SRT]({download_links['srt']})\n"
    if "json" in download_links:
        text += f"🔧 [JSON]({download_links['json']})\n"
    
    await callback.message.answer(text, parse_mode="Markdown")

# History list window
history_list_window = Window(
    Const("📜 История транскрипций"),
    Format("Страница {page}/{total_pages}"),
    Format("У вас пока нет истории транскрипций.", when="empty"),
    Group(
        Select(
            Format("{item[file_name]} ({item[duration]}) - {item[status]}"),
            id="history_select",
            item_id_getter=lambda item: item["id"],
            items="history_items",
            on_click=on_item_selected
        ),
        width=1,
        when=lambda data, widget, manager: not data.get("empty")
    ),
    Row(
        Button(
            Const("⬅️"),
            id="prev_page",
            on_click=lambda c, b, m: on_page_changed(c, b, m, -1),
            when="has_prev"
        ),
        Button(
            Const("➡️"),
            id="next_page",
            on_click=lambda c, b, m: on_page_changed(c, b, m, 1),
            when="has_next"
        ),
    ),
    Row(
        Cancel(Const("🔙 Назад"))
    ),
    state=HistoryState.list,
    getter=history_list_getter
)

# History detail window
history_detail_window = Window(
    Format("📋 Детали транскрипции\n\n"
           "Файл: {file_name}\n"
           "Дата: {date}\n"
           "Длительность: {duration}\n"
           "Статус: {status}\n"
           "Модель: {model}\n"
           "Язык: {language}\n"
           "Диаризация: {diarization}\n"
           "Количество спикеров: {speakers_count}"),
    Format("❌ Ошибка: {error_message}", when="is_failed"),
    Row(
        Button(
            Const("📥 Скачать результаты"),
            id="download_results",
            on_click=on_download_result,
            when="is_completed"
        ),
    ),
    Row(
        Button(
            Const("🔄 Повторить транскрипцию"),
            id="retry_transcription",
            on_click=lambda c, b, m: m.start(MainMenuState.main),  # Placeholder, would actually start a new transcription
            when="is_failed"
        ),
    ),
    Row(
        SwitchTo(
            Const("🔙 К списку"),
            id="back_to_list",
            state=HistoryState.list
        )
    ),
    state=HistoryState.detail,
    getter=history_detail_getter
)

# Create dialog
history_dialog = Dialog(history_list_window, history_detail_window)
```

#### Модели данных для пользовательских настроек

```python
# src/domains/user/models.py
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship

from src.infrastructure.database.base import Base

class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    history = relationship("TranscriptionHistory", back_populates="user", cascade="all, delete-orphan")

class UserSettings(Base):
    """User settings model."""
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model = Column(String, default="whisper-large-v3")
    language = Column(String, default="auto")
    diarization = Column(Boolean, default=True)
    export_format = Column(String, default="all")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="settings")

class TranscriptionHistory(Base):
    """Transcription history model."""
    __tablename__ = "transcription_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(String, nullable=False)
    file_id = Column(String, nullable=False)
    file_name = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)
    model = Column(String, nullable=True)
    language = Column(String, nullable=True)
    diarization = Column(Boolean, default=True)
    status = Column(String, default="pending")
    error_message = Column(String, nullable=True)
    result_path = Column(String, nullable=True)
    speakers_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="history")
```

#### Сервисы для работы с пользовательскими данными

```python
# src/domains/user/services.py
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.user.models import User, UserSettings, TranscriptionHistory
from src.infrastructure.database.session import get_session

class UserService:
    """Service for user operations."""
    
    async def get_or_create_user(self, telegram_id: int, username: Optional[str] = None,
                               first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
        """Get or create a user by Telegram ID."""
        async with get_session() as session:
            # Check if user exists
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalars().first()
            
            if not user:
                # Create new user
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(user)
                
                # Create default settings
                settings = UserSettings(user=user)
                session.add(settings)
                
                await session.commit()
                await session.refresh(user)
            
            return user
    
    async def get_user_settings(self, telegram_id: int) -> Dict[str, Any]:
        """Get user settings."""
        async with get_session() as session:
            # Get user
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalars().first()
            
            if not user:
                # Create user with default settings
                return await self.get_or_create_user(telegram_id)
            
            # Get settings
            result = await session.execute(
                select(UserSettings).where(UserSettings.user_id == user.id)
            )
            settings = result.scalars().first()
            
            if not settings:
                # Create default settings
                settings = UserSettings(user=user)
                session.add(settings)
                await session.commit()
                await session.refresh(settings)
            
            # Convert to dict
            return {
                "model": settings.model,
                "language": settings.language,
                "diarization": settings.diarization,
                "export_format": settings.export_format
            }
    
    async def update_user_settings(self, telegram_id: int, settings: Dict[str, Any]) -> None:
        """Update user settings."""
        async with get_session() as session:
            # Get user
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalars().first()
            
            if not user:
                # Create user with default settings
                user = await self.get_or_create_user(telegram_id)
            
            # Get settings
            result = await session.execute(
                select(UserSettings).where(UserSettings.user_id == user.id)
            )
            user_settings = result.scalars().first()
            
            if not user_settings:
                # Create default settings
                user_settings = UserSettings(user=user)
                session.add(user_settings)
            
            # Update settings
            for key, value in settings.items():
                if hasattr(user_settings, key):
                    setattr(user_settings, key, value)
            
            await session.commit()
    
    async def add_history_item(self, telegram_id: int, task_data: Dict[str, Any]) -> None:
        """Add item to user's transcription history."""
        async with get_session() as session:
            # Get user
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalars().first()
            
            if not user:
                # Create user with default settings
                user = await self.get_or_create_user(telegram_id)
            
            # Create history item
            history_item = TranscriptionHistory(
                user_id=user.id,
                task_id=task_data.get("task_id"),
                file_id=task_data.get("file_id"),
                file_name=task_data.get("file_name"),
                file_size=task_data.get("file_size"),
                duration=task_data.get("duration"),
                model=task_data.get("model"),
                language=task_data.get("language"),
                diarization=task_data.get("diarization", True),
                status=task_data.get("status", "pending")
            )
            session.add(history_item)
            await session.commit()
    
    async def update_history_item(self, task_id: str, update_data: Dict[str, Any]) -> None:
        """Update history item."""
        async with get_session() as session:
            # Get history item
            result = await session.execute(
                select(TranscriptionHistory).where(TranscriptionHistory.task_id == task_id)
            )
            history_item = result.scalars().first()
            
            if history_item:
                # Update fields
                for key, value in update_data.items():
                    if hasattr(history_item, key):
                        setattr(history_item, key, value)
                
                await session.commit()
    
    async def get_user_history(self, telegram_id: int, page: int = 1, 
                             items_per_page: int = 10) -> List[Dict[str, Any]]:
        """Get user's transcription history with pagination."""
        async with get_session() as session:
            # Get user
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalars().first()
            
            if not user:
                return []
            
            # Get history items with pagination
            offset = (page - 1) * items_per_page
            result = await session.execute(
                select(TranscriptionHistory)
                .where(TranscriptionHistory.user_id == user.id)
                .order_by(desc(TranscriptionHistory.created_at))
                .offset(offset)
                .limit(items_per_page)
            )
            history_items = result.scalars().all()
            
            # Convert to list of dicts
            return [
                {
                    "id": item.task_id,
                    "file_name": item.file_name,
                    "file_size": item.file_size,
                    "duration": item.duration,
                    "model": item.model,
                    "language": item.language,
                    "diarization": item.diarization,
                    "status": item.status,
                    "error_message": item.error_message,
                    "created_at": item.created_at,
                    "speakers_count": item.speakers_count
                }
                for item in history_items
            ]
    
    async def get_user_history_count(self, telegram_id: int) -> int:
        """Get count of user's history items."""
        async with get_session() as session:
            # Get user
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalars().first()
            
            if not user:
                return 0
            
            # Get count
            result = await session.execute(
                select(TranscriptionHistory)
                .where(TranscriptionHistory.user_id == user.id)
            )
            return len(result.scalars().all())
```

### Конфигурации

#### Настройка состояний для диалогов

```python
# src/bot/states.py
from aiogram.fsm.state import State, StatesGroup

class MainMenuState(StatesGroup):
    """Main menu states."""
    main = State()

class TranscriptionState(StatesGroup):
    """Transcription states."""
    upload = State()
    confirm = State()

class SettingsState(StatesGroup):
    """Settings states."""
    main = State()

class HistoryState(StatesGroup):
    """History states."""
    list = State()
    detail = State()

class ProgressState(StatesGroup):
    """Progress tracking states."""
    tracking = State()
```

#### Настройка бота с диалогами

```python
# src/bot/setup.py
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand

from src.bot.dialogs.registry import setup_dialogs
from src.bot.handlers.commands import register_command_handlers
from src.bot.handlers.callbacks import register_callback_handlers
from src.bot.handlers.messages import register_message_handlers
from src.config import settings

async def setup_bot():
    """Setup bot and dispatcher."""
    # Create storage
    storage = RedisStorage.from_url(settings.REDIS_URL)
    
    # Create bot and dispatcher
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=storage)
    
    # Register handlers
    register_command_handlers(dp)
    register_callback_handlers(dp)
    register_message_handlers(dp)
    
    # Setup dialogs
    dialog_registry = setup_dialogs(dp)
    
    # Set bot commands
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="settings", description="Настройки"),
        BotCommand(command="history", description="История транскрипций"),
    ])
    
    return bot, dp
```

### Схемы данных/API

#### Схемы для пользовательских настроек

```python
# src/domains/user/schemas.py
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class UserSettingsCreate(BaseModel):
    """Schema for creating user settings."""
    model: str = Field(default="whisper-large-v3")
    language: str = Field(default="auto")
    diarization: bool = Field(default=True)
    export_format: str = Field(default="all")

class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings."""
    model: Optional[str] = None
    language: Optional[str] = None
    diarization: Optional[bool] = None
    export_format: Optional[str] = None

class UserSettings(BaseModel):
    """Schema for user settings."""
    model: str
    language: str
    diarization: bool
    export_format: str
    
    class Config:
        orm_mode = True

class TranscriptionHistoryItem(BaseModel):
    """Schema for transcription history item."""
    id: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[float] = None
    model: Optional[str] = None
    language: Optional[str] = None
    diarization: bool = True
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    speakers_count: Optional[int] = None
    
    class Config:
        orm_mode = True

class TranscriptionHistoryList(BaseModel):
    """Schema for list of transcription history items."""
    items: List[TranscriptionHistoryItem]
    total: int
    page: int
    pages: int
```

## 2. Практическая секция

### Пошаговые инструкции

1. **Настройка базовой структуры диалогов**
   - Создайте модуль `src/bot/states.py` для определения состояний диалогов
   - Создайте модуль `src/bot/dialogs` для хранения диалогов
   - Реализуйте базовую структуру диалогов с главным меню

2. **Реализация диалога транскрипции**
   - Создайте диалог для загрузки аудиофайлов
   - Добавьте валидацию файлов и отображение информации о файле
   - Реализуйте подтверждение перед началом транскрипции

3. **Реализация прогресс-бара**
   - Создайте диалог для отображения прогресса обработки
   - Реализуйте механизм обновления прогресса в реальном времени
   - Добавьте возможность отмены задачи

4. **Настройка пользовательских настроек**
   - Создайте модели данных для хранения настроек пользователя
   - Реализуйте диалог для изменения настроек
   - Добавьте сохранение настроек в базу данных

5. **Реализация истории обработки**
   - Создайте модели данных для хранения истории транскрипций
   - Реализуйте диалог для просмотра истории с пагинацией
   - Добавьте детальный просмотр результатов транскрипции

6. **Интеграция с сервисами обработки**
   - Свяжите диалоги с сервисами транскрипции и диаризации
   - Реализуйте обновление статуса задач в реальном времени
   - Добавьте обработку ошибок и уведомления пользователя

7. **Настройка миграций базы данных**
   - Создайте миграции для новых моделей данных
   - Проверьте корректность работы миграций
   - Добавьте индексы для оптимизации запросов

8. **Тестирование и отладка**
   - Проверьте работу всех диалогов
   - Протестируйте обработку ошибок
   - Убедитесь в корректной работе прогресс-баров и уведомлений

### Частые ошибки (Common Pitfalls)

1. **Блокировка основного потока при обновлении прогресса**
   - Используйте асинхронные задачи для обновления прогресса
   - Не блокируйте обработку сообщений пользователя
   - Применяйте `asyncio.create_task()` для фоновых операций

2. **Утечки памяти при длительных операциях**
   - Правильно закрывайте сессии базы данных
   - Используйте контекстные менеджеры для ресурсов
   - Не храните большие объекты в памяти без необходимости

3. **Проблемы с конкурентным доступом к данным**
   - Используйте блокировки или транзакции для критических секций
   - Избегайте гонок данных при обновлении статуса задач
   - Применяйте атомарные операции для обновления счетчиков

4. **Неправильная обработка ошибок в диалогах**
   - Всегда обрабатывайте исключения в обработчиках диалогов
   - Предоставляйте понятные сообщения об ошибках пользователю
   - Логируйте ошибки для дальнейшего анализа

5. **Проблемы с пагинацией в истории**
   - Правильно рассчитывайте смещение и лимит для запросов
   - Учитывайте пустые результаты и граничные случаи
   - Кешируйте результаты для улучшения производительности

### Советы по оптимизации (Performance Tips)

1. **Оптимизация запросов к базе данных**
   - Используйте индексы для часто запрашиваемых полей
   - Применяйте JOIN вместо множественных запросов
   - Ограничивайте количество возвращаемых полей

2. **Кеширование данных пользователя**
   - Кешируйте настройки пользователя в Redis
   - Используйте TTL для автоматического обновления кеша
   - Инвалидируйте кеш при изменении настроек

3. **Эффективное обновление прогресса**
   - Обновляйте прогресс не чаще, чем раз в секунду
   - Используйте дебаунсинг для предотвращения частых обновлений
   - Группируйте обновления для уменьшения нагрузки

4. **Оптимизация хранения истории**
   - Архивируйте старые записи истории
   - Используйте партиционирование таблиц для больших объемов данных
   - Реализуйте автоматическую очистку старых записей

5. **Улучшение пользовательского опыта**
   - Предварительно загружайте данные для уменьшения задержек
   - Используйте анимированные эмодзи для индикации прогресса
   - Добавьте кнопки быстрого доступа к часто используемым функциям

## 3. Валидационная секция

### Чек-лист для самопроверки

- [ ] Реализованы все необходимые диалоги (главное меню, транскрипция, настройки, история)
- [ ] Прогресс-бары корректно отображают статус обработки в реальном времени
- [ ] Пользовательские настройки сохраняются и применяются к новым транскрипциям
- [ ] История транскрипций отображается с пагинацией и возможностью просмотра деталей
- [ ] Реализована возможность отмены задач и повторной обработки
- [ ] Все диалоги имеют интуитивно понятный интерфейс с подсказками
- [ ] Обработка ошибок реализована на всех уровнях с понятными сообщениями
- [ ] Настройки пользователя сохраняются в базе данных и корректно загружаются
- [ ] Реализована система уведомлений о завершении задач
- [ ] Код соответствует стандартам PEP 8 и имеет типизацию

### Автоматизированные тесты

```python
# tests/bot/test_dialogs.py
import pytest
from unittest.mock import AsyncMock, patch

from aiogram.types import Message, User as TelegramUser, Chat
from aiogram_dialog import DialogManager
from aiogram_dialog.test_tools import BotClient, MockMessageManager

from src.bot.dialogs.main_menu import main_menu_dialog
from src.bot.dialogs.settings import settings_dialog
from src.bot.dialogs.history import history_dialog
from src.bot.dialogs.progress import progress_dialog
from src.bot.states import MainMenuState, SettingsState, HistoryState, ProgressState

@pytest.fixture
def telegram_user():
    return TelegramUser(id=123456, is_bot=False, first_name="Test", username="test_user")

@pytest.fixture
def chat():
    return Chat(id=123456, type="private")

@pytest.fixture
def message(telegram_user, chat):
    return Message(message_id=1, date=1234567890, chat=chat, from_user=telegram_user)

@pytest.fixture
async def dialog_manager():
    manager = AsyncMock(spec=DialogManager)
    manager.dialog_data = {}
    manager.start = AsyncMock()
    manager.switch_to = AsyncMock()
    manager.update = AsyncMock()
    return manager

@pytest.mark.asyncio
async def test_main_menu_dialog(dialog_manager, message):
    """Test main menu dialog."""
    # Test start handler
    from src.bot.dialogs.main_menu import start_handler
    await start_handler(message, dialog_manager)
    dialog_manager.start.assert_called_once_with(MainMenuState.main)
    
    # Test navigation to transcription
    from src.bot.dialogs.main_menu import on_transcribe_selected
    await on_transcribe_selected(None, None, dialog_manager)
    dialog_manager.start.assert_called_with(TranscriptionState.upload)
    
    # Test navigation to settings
    from src.bot.dialogs.main_menu import on_settings_selected
    await on_settings_selected(None, None, dialog_manager)
    dialog_manager.start.assert_called_with(SettingsState.main)
    
    # Test navigation to history
    from src.bot.dialogs.main_menu import on_history_selected
    await on_history_selected(None, None, dialog_manager)
    dialog_manager.start.assert_called_with(HistoryState.list)

@pytest.mark.asyncio
async def test_settings_dialog(dialog_manager):
    """Test settings dialog."""
    # Mock user service
    user_service = AsyncMock()
    user_service.get_user_settings.return_value = {
        "model": "whisper-large-v3",
        "language": "auto",
        "diarization": True,
        "export_format": "all"
    }
    
    # Test settings getter
    from src.bot.dialogs.settings import settings_getter
    dialog_manager.event.from_user.id = 123456
    result = await settings_getter(dialog_manager, user_service=user_service)
    
    assert result["model"] == "whisper-large-v3"
    assert result["language"] == "auto"
    assert result["diarization"] is True
    assert result["export_format"] == "all"
    
    # Test model change
    from src.bot.dialogs.settings import on_model_changed
    callback = AsyncMock()
    callback.from_user.id = 123456
    await on_model_changed(callback, None, dialog_manager, "whisper-turbo")
    
    user_service.update_user_settings.assert_called_once_with(
        123456, {"model": "whisper-turbo"}
    )
    dialog_manager.update.assert_called_once()

@pytest.mark.asyncio
async def test_progress_dialog(dialog_manager):
    """Test progress dialog."""
    # Mock transcription service
    transcription_service = AsyncMock()
    transcription_service.get_task_status.return_value = {
        "progress": 0.5,
        "status": "processing",
        "status_message": "Обработка аудио...",
    }
    
    # Test progress getter
    from src.bot.dialogs.progress import progress_getter
    dialog_manager.dialog_data["task_id"] = "test-task-id"
    result = await progress_getter(dialog_manager, transcription_service=transcription_service)
    
    assert result["progress"] == 50
    assert result["status"] == "Обработка аудио..."
    assert result["progress_bar"] == "🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜"
    assert result["is_completed"] is False
    assert result["is_failed"] is False
    
    # Test completed task
    transcription_service.get_task_status.return_value = {
        "progress": 1.0,
        "status": "completed",
        "status_message": "Транскрипция завершена",
        "result": {"text": "Test transcription"}
    }
    
    result = await progress_getter(dialog_manager, transcription_service=transcription_service)
    
    assert result["progress"] == 100
    assert result["status"] == "Транскрипция завершена"
    assert result["progress_bar"] == "🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩"
    assert result["is_completed"] is True
    assert dialog_manager.dialog_data["stop_polling"] is True
    assert dialog_manager.dialog_data["result"] == {"text": "Test transcription"}
```

### Критерии для ручного тестирования

1. **Тестирование навигации по меню**
   - Запустите бота и проверьте отображение главного меню
   - Проверьте переходы между разделами (транскрипция, настройки, история)
   - Убедитесь, что кнопки "Назад" работают корректно во всех диалогах

2. **Тестирование загрузки файлов**
   - Загрузите аудиофайлы разных форматов (mp3, wav, ogg, m4a)
   - Проверьте обработку файлов разного размера
   - Убедитесь, что отображается корректная информация о файле

3. **Тестирование прогресс-баров**
   - Запустите транскрипцию и проверьте отображение прогресса
   - Убедитесь, что прогресс обновляется в реальном времени
   - Проверьте возможность отмены задачи во время обработки

4. **Тестирование настроек пользователя**
   - Измените различные настройки (модель, язык, диаризация)
   - Проверьте, что настройки сохраняются между сессиями
   - Убедитесь, что настройки применяются к новым транскрипциям

5. **Тестирование истории транскрипций**
   - Проверьте отображение списка транскрипций с пагинацией
   - Просмотрите детали транскрипции и скачайте результаты
   - Убедитесь, что история корректно обновляется после новых транскрипций

6. **Тестирование обработки ошибок**
   - Загрузите неподдерживаемый формат файла
   - Проверьте обработку слишком больших файлов
   - Убедитесь, что отображаются понятные сообщения об ошибках

7. **Тестирование производительности**
   - Проверьте время отклика бота при большом количестве запросов
   - Оцените скорость загрузки истории с большим количеством записей
   - Убедитесь, что бот работает стабильно при длительном использовании