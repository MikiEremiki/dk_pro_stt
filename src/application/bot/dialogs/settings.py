from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Select, Back
from aiogram_dialog.widgets.text import Const, Format

from src.domains.user.entities import UserSettings
from src.domains.user.repositories import UserSettingsRepository
from src.domains.export.entities import ExportFormat
from src.domains.transcription.entities import TranscriptionModel
from src.domains.user.services import UserSettingsService


# Состояния диалога
class SettingsDialog(StatesGroup):
    settings = State()
    model = State()
    export = State()


# Обработчики
async def get_settings_data(dialog_manager: DialogManager, **kwargs):
    """Get user settings data."""
    user_id = dialog_manager.event.from_user.id
    user_service = UserSettingsService(UserSettingsRepository())
    settings = UserSettings(user_id)
    print(settings)
    return {
        "preferred_model": settings.preferred_model,
        "preferred_export_format": settings.preferred_export_format,
        "auto_detect_language": 'Вкл' if settings.auto_detect_language else 'Выкл',
        "auto_delete_files": 'Вкл' if settings.auto_delete_files else 'Выкл',
    }


async def on_model_selected(
    callback: CallbackQuery, 
    widget: Select, 
    dialog_manager: DialogManager, 
    item_id: str,
):
    """Handle model selection."""
    user_id = callback.from_user.id
    # user_service = UserSettingsService()
    # await user_service.update_user_settings(
    #     user_id, preferred_model=TranscriptionModel(item_id))
    await callback.answer(f"Модель {item_id} выбрана")
    await dialog_manager.update({"preferred_model": item_id})


async def on_export_selected(
    callback: CallbackQuery, 
    widget: Select, 
    dialog_manager: DialogManager, 
    item_id: str,
):
    """Handle export format selection."""
    user_id = callback.from_user.id
    # user_service = UserSettingsService()
    # await user_service.update_user_settings(
    #     user_id, preferred_export_format=ExportFormat(item_id))
    await callback.answer(f"Формат экспорта {item_id} выбран")
    await dialog_manager.update({"preferred_export_format": item_id})


async def toggle_auto_detect(
    callback: CallbackQuery, 
    button: Button, 
    dialog_manager: DialogManager,
):
    """Toggle auto detect language setting."""
    user_id = callback.from_user.id
    current = dialog_manager.dialog_data.get("auto_detect_language", True)
    # user_service = UserSettingsService()
    new_value = not current
    # await user_service.update_user_settings(user_id, auto_detect_language=new_value)
    await dialog_manager.update({"auto_detect_language": new_value})


async def toggle_auto_delete(
    callback: CallbackQuery, 
    button: Button, 
    dialog_manager: DialogManager,
):
    """Toggle auto delete files setting."""
    user_id = callback.from_user.id
    current = dialog_manager.dialog_data.get("auto_delete_files", True)
    # user_service = UserSettingsService()
    new_value = not current
    # await user_service.update_user_settings(user_id, auto_delete_files=new_value)
    await dialog_manager.update({"auto_delete_files": new_value})


# Окна диалога
settings_window = Window(
    Const("⚙️ Настройки"),
    Const("Здесь вы можете настроить параметры транскрипции и экспорта."),
    Button(
        Format("🔄 Модель транскрипции: {preferred_model}"),
        id="model",
        on_click=lambda c, b, m: m.switch_to(SettingsDialog.model)
    ),
    Button(
        Format("📤 Формат экспорта: {preferred_export_format}"),
        id="export",
        on_click=lambda c, b, m: m.switch_to(SettingsDialog.export)
    ),
    Button(
        Format("🔍 Автоопределение языка: {auto_detect_language}"),
        id="auto_detect",
        on_click=toggle_auto_detect
    ),
    Button(
        Format("🗑 Автоудаление файлов: {auto_delete_files}"),
        id="auto_delete",
        on_click=toggle_auto_delete
    ),
    Button(
        Const("✅ Готово"),
        id="done",
        on_click=lambda c, b, m: m.done()
    ),
    state=SettingsDialog.settings,
    getter=get_settings_data
)

model_window = Window(
    Const("🔄 Выберите модель транскрипции"),
    Const("От выбора модели зависит качество и скорость транскрипции."),
    Select(
        Format("✓ {item}") if Format("{item}") == Format("{preferred_model}") else Format("{item}"),
        id="model_select",
        items=["whisper-large-v3", "whisper-turbo"],
        item_id_getter=lambda x: x,
        on_click=on_model_selected
    ),
    Back(Const("◀️ Назад")),
    state=SettingsDialog.model,
    getter=get_settings_data
)

export_window = Window(
    Const("📤 Выберите формат экспорта по умолчанию"),
    Select(
        Format("✓ {item}") if Format("{item}") == Format("{preferred_export_format}") else Format("{item}"),
        id="export_select",
        items=["docx", "srt", "json", "txt"],
        item_id_getter=lambda x: x,
        on_click=on_export_selected
    ),
    Back(Const("◀️ Назад")),
    state=SettingsDialog.export,
    getter=get_settings_data
)

# Создание диалога
settings_dialog = Dialog(settings_window, model_window, export_window)