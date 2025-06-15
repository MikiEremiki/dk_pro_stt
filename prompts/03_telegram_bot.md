# Фаза 1, День 3. Базовый Telegram бот с диалогами

## Цель (Definition of Done)
- Создан базовый Telegram бот с использованием aiogram 3.x
- Настроены основные команды бота (/start, /help, /settings)
- Реализованы диалоги с использованием aiogram-dialog
- Настроена обработка голосовых сообщений и аудиофайлов
- Реализована базовая структура обработчиков и middleware

## Ссылки на документацию
- [aiogram 3.x Documentation](https://docs.aiogram.dev/en/latest/)
- [aiogram-dialog Documentation](https://github.com/Tishka17/aiogram_dialog)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [structlog Documentation](https://www.structlog.org/en/stable/)

---

### 1. Техническая секция

#### Описание
В этом задании необходимо создать базовый Telegram бот с использованием aiogram 3.x и aiogram-dialog для реализации интерактивных диалогов. Бот должен уметь принимать голосовые сообщения и аудиофайлы, а также предоставлять пользователю информацию о процессе обработки.

Основные компоненты:
1. **Базовый бот** - настройка бота, обработка команд, логирование
2. **Диалоги** - интерактивные диалоги для взаимодействия с пользователем
3. **Обработка медиа** - прием и валидация голосовых сообщений и аудиофайлов
4. **Middleware** - логирование, аутентификация, обработка ошибок

#### Примеры кода

**Основная структура бота:**
```python
# src/application/bot/main.py
import asyncio
import logging
import structlog
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_dialog import DialogRegistry

from src.config.settings import config
from src.application.bot.handlers import register_handlers
from src.application.bot.middlewares import register_middlewares
from src.application.bot.dialogs import register_dialogs


# Настройка логирования
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()


async def main():
    # Настройка хранилища состояний
    storage = RedisStorage.from_url(config.REDIS_URL)
    
    # Создание экземпляра бота и диспетчера
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=storage)
    
    # Регистрация диалогов
    dialog_registry = DialogRegistry(dp)
    register_dialogs(dialog_registry)
    
    # Регистрация middleware
    register_middlewares(dp)
    
    # Регистрация обработчиков
    register_handlers(dp)
    
    # Запуск бота
    logger.info("Starting bot")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```

**Регистрация обработчиков:**
```python
# src/application/bot/handlers/__init__.py
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
```

**Обработчики команд:**
```python
# src/application/bot/handlers/commands.py
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
```

**Обработчики аудио:**
```python
# src/application/bot/handlers/audio.py
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


async def handle_voice(
    message: Message, 
    dialog_manager: DialogManager, 
    audio_service: AudioService
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
    
    # Запуск диалога транскрипции
    await dialog_manager.start(
        TranscriptionDialog.transcription,
        data={"file_id": file_id, "file_name": file_name, "user_id": message.from_user.id},
        mode=StartMode.RESET_STACK
    )


def register_audio_handlers(dp: Dispatcher):
    """Register audio handlers."""
    dp.message.register(handle_audio, F.audio)
    dp.message.register(handle_voice, F.voice)
```

**Middleware для логирования:**
```python
# src/application/bot/middlewares/logging.py
import structlog
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User


logger = structlog.get_logger()


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging all updates."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получение информации о пользователе
        user = data.get("event_from_user", None)
        if user and isinstance(user, User):
            user_info = {
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        else:
            user_info = {"user_id": "unknown"}
        
        # Логирование события
        logger.info(
            "Received update",
            update_type=event.__class__.__name__,
            **user_info
        )
        
        # Вызов следующего обработчика
        return await handler(event, data)
```

**Диалог настроек:**
```python
# src/application/bot/dialogs/settings.py
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Select, Back
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput

from src.domains.user.services import UserService


# Состояния диалога
class SettingsDialog:
    settings = "settings"
    model = "settings_model"
    export = "settings_export"


# Обработчики
async def get_settings_data(dialog_manager: DialogManager, user_service: UserService, **kwargs):
    """Get user settings data."""
    user_id = dialog_manager.event.from_user.id
    settings = await user_service.get_user_settings(user_id)
    
    return {
        "preferred_model": settings.preferred_model,
        "preferred_export_format": settings.preferred_export_format,
        "auto_detect_language": settings.auto_detect_language,
        "auto_delete_files": settings.auto_delete_files,
    }


async def on_model_selected(
    callback: CallbackQuery, 
    widget: Select, 
    dialog_manager: DialogManager, 
    item_id: str,
    user_service: UserService
):
    """Handle model selection."""
    user_id = callback.from_user.id
    await user_service.update_user_settings(user_id, preferred_model=item_id)
    await callback.answer(f"Модель {item_id} выбрана")
    await dialog_manager.update({"preferred_model": item_id})


async def on_export_selected(
    callback: CallbackQuery, 
    widget: Select, 
    dialog_manager: DialogManager, 
    item_id: str,
    user_service: UserService
):
    """Handle export format selection."""
    user_id = callback.from_user.id
    await user_service.update_user_settings(user_id, preferred_export_format=item_id)
    await callback.answer(f"Формат экспорта {item_id} выбран")
    await dialog_manager.update({"preferred_export_format": item_id})


async def toggle_auto_detect(
    callback: CallbackQuery, 
    button: Button, 
    dialog_manager: DialogManager,
    user_service: UserService
):
    """Toggle auto detect language setting."""
    user_id = callback.from_user.id
    current = dialog_manager.dialog_data.get("auto_detect_language", True)
    new_value = not current
    await user_service.update_user_settings(user_id, auto_detect_language=new_value)
    await dialog_manager.update({"auto_detect_language": new_value})


async def toggle_auto_delete(
    callback: CallbackQuery, 
    button: Button, 
    dialog_manager: DialogManager,
    user_service: UserService
):
    """Toggle auto delete files setting."""
    user_id = callback.from_user.id
    current = dialog_manager.dialog_data.get("auto_delete_files", True)
    new_value = not current
    await user_service.update_user_settings(user_id, auto_delete_files=new_value)
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
        Format("🔍 Автоопределение языка: {'Вкл' if auto_detect_language else 'Выкл'}"),
        id="auto_detect",
        on_click=toggle_auto_detect
    ),
    Button(
        Format("🗑 Автоудаление файлов: {'Вкл' if auto_delete_files else 'Выкл'}"),
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
```

**Диалог транскрипции:**
```python
# src/application/bot/dialogs/transcription.py
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Select, Row, Column, Group
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput

from src.domains.audio.services import AudioService
from src.domains.transcription.services import TranscriptionService
from src.domains.diarization.services import DiarizationService
from src.domains.export.services import ExportService


# Состояния диалога
class TranscriptionDialog:
    transcription = "transcription"
    processing = "transcription_processing"
    result = "transcription_result"
    export = "transcription_export"


# Обработчики
async def start_transcription(dialog_manager: DialogManager, **kwargs):
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
    export_service: ExportService
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
```

**Регистрация диалогов:**
```python
# src/application/bot/dialogs/__init__.py
from aiogram_dialog import DialogRegistry

from .settings import settings_dialog
from .help import help_dialog
from .transcription import transcription_dialog


def register_dialogs(registry: DialogRegistry):
    """Register all dialogs."""
    registry.register(settings_dialog)
    registry.register(help_dialog)
    registry.register(transcription_dialog)
```

**Обработка ошибок:**
```python
# src/application/bot/handlers/errors.py
import structlog
from aiogram import Dispatcher
from aiogram.types import ErrorEvent
from aiogram.exceptions import TelegramAPIError


logger = structlog.get_logger()


async def handle_errors(error: ErrorEvent, bot):
    """Handle errors in update processing."""
    # Получение информации об ошибке
    exception = error.exception
    
    # Логирование ошибки
    logger.error(
        "Error while processing update",
        exception=str(exception),
        update=error.update.model_dump() if error.update else None,
    )
    
    # Обработка различных типов ошибок
    if isinstance(exception, TelegramAPIError):
        # Ошибки API Telegram
        logger.error("Telegram API error", code=exception.status_code)
    else:
        # Другие ошибки
        logger.exception("Unhandled exception")
    
    # Отправка сообщения пользователю, если возможно
    if error.update and hasattr(error.update, "message"):
        try:
            await bot.send_message(
                error.update.message.chat.id,
                "⚠️ Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже."
            )
        except Exception as e:
            logger.error("Failed to send error message to user", exception=str(e))


def register_error_handlers(dp: Dispatcher):
    """Register error handlers."""
    dp.errors.register(handle_errors)
```

#### Схемы данных/API

**Структура обработки аудио:**
```
1. Пользователь отправляет аудиофайл или голосовое сообщение
2. Бот проверяет размер и формат файла
3. Бот запускает диалог транскрипции
4. Файл загружается и обрабатывается
5. Пользователь получает результат транскрипции
6. Пользователь может выбрать формат экспорта
```

**Структура команд бота:**
```
/start - Начало работы с ботом
/help - Получение справки
/settings - Настройка параметров транскрипции и экспорта
```

**Структура диалогов:**
```
1. Диалог настроек (SettingsDialog)
   - Основное окно настроек
   - Выбор модели транскрипции
   - Выбор формата экспорта

2. Диалог справки (HelpDialog)
   - Информация о боте
   - Инструкции по использованию

3. Диалог транскрипции (TranscriptionDialog)
   - Начало транскрипции
   - Процесс обработки с прогресс-баром
   - Результаты транскрипции
   - Экспорт результатов
```

### 2. Практическая секция

#### Пошаговые инструкции

1. **Настройка базового бота:**
   - Создайте структуру каталогов для бота
   - Настройте логирование с использованием structlog
   - Создайте основной файл бота с диспетчером и хранилищем состояний

2. **Реализация обработчиков команд:**
   - Создайте обработчики для команд /start, /help, /settings
   - Реализуйте регистрацию обработчиков в диспетчере
   - Добавьте базовые ответы на команды

3. **Реализация обработчиков медиа:**
   - Создайте обработчики для аудиофайлов и голосовых сообщений
   - Добавьте валидацию размера и формата файлов
   - Реализуйте базовую логику обработки файлов

4. **Настройка диалогов:**
   - Создайте диалог настроек с возможностью выбора модели и формата экспорта
   - Реализуйте диалог транскрипции с отображением прогресса
   - Добавьте диалог справки с информацией о боте

5. **Реализация middleware:**
   - Создайте middleware для логирования запросов
   - Добавьте middleware для аутентификации пользователей
   - Реализуйте middleware для обработки ошибок

6. **Тестирование бота:**
   - Запустите бота в режиме разработки
   - Проверьте работу всех команд и диалогов
   - Убедитесь, что обработка ошибок работает корректно

#### Частые ошибки (Common Pitfalls)

1. **Проблемы с aiogram 3.x:**
   - Использование устаревшего API из aiogram 2.x
   - Неправильная работа с фильтрами и обработчиками
   - Проблемы с асинхронными обработчиками

2. **Проблемы с диалогами:**
   - Неправильная структура состояний диалога
   - Отсутствие обработчиков для кнопок
   - Проблемы с передачей данных между окнами диалога

3. **Проблемы с обработкой файлов:**
   - Неправильная работа с file_id и file_path
   - Отсутствие проверки размера и формата файлов
   - Проблемы с загрузкой больших файлов

#### Советы по оптимизации (Performance Tips)

1. **Оптимизация работы с Telegram API:**
   - Используйте асинхронные запросы для загрузки файлов
   - Применяйте кэширование для часто используемых данных
   - Используйте webhook вместо long polling в production

2. **Оптимизация диалогов:**
   - Минимизируйте количество обновлений состояния диалога
   - Используйте кэширование данных в диалогах
   - Применяйте ленивую загрузку данных

3. **Оптимизация обработки ошибок:**
   - Используйте структурированное логирование
   - Добавьте контекст к сообщениям об ошибках
   - Реализуйте механизм повторных попыток для нестабильных операций

### 3. Валидационная секция

#### Чек-лист для самопроверки

- [ ] Бот успешно запускается и отвечает на команды
- [ ] Реализованы обработчики для команд /start, /help, /settings
- [ ] Работает прием и валидация аудиофайлов и голосовых сообщений
- [ ] Диалоги корректно отображаются и обрабатывают действия пользователя
- [ ] Middleware для логирования и обработки ошибок работает корректно
- [ ] Код соответствует PEP 8 и включает типизацию
- [ ] Логирование настроено и работает корректно
- [ ] Обработка ошибок реализована и тестируется
- [ ] Бот корректно работает с Redis для хранения состояний
- [ ] Документация к коду добавлена и актуальна

#### Автоматизированные тесты

```python
# tests/application/bot/test_commands.py
import pytest
from unittest.mock import AsyncMock, patch

from aiogram.types import Message, User, Chat
from aiogram_dialog import DialogManager

from src.application.bot.handlers.commands import cmd_start, cmd_help, cmd_settings


@pytest.fixture
def message():
    """Create a mock message."""
    message = AsyncMock(spec=Message)
    message.from_user = User(id=123456789, is_bot=False, first_name="Test")
    message.chat = Chat(id=123456789, type="private")
    return message


@pytest.fixture
def dialog_manager():
    """Create a mock dialog manager."""
    return AsyncMock(spec=DialogManager)


async def test_cmd_start(message, dialog_manager):
    """Test the /start command handler."""
    await cmd_start(message, dialog_manager)
    message.answer.assert_called_once()
    assert "Привет" in message.answer.call_args[0][0]


async def test_cmd_help(message, dialog_manager):
    """Test the /help command handler."""
    await cmd_help(message, dialog_manager)
    dialog_manager.start.assert_called_once()


async def test_cmd_settings(message, dialog_manager):
    """Test the /settings command handler."""
    await cmd_settings(message, dialog_manager)
    dialog_manager.start.assert_called_once()


# tests/application/bot/test_audio.py
import pytest
from unittest.mock import AsyncMock, patch

from aiogram.types import Message, User, Chat, Audio, Voice
from aiogram_dialog import DialogManager

from src.application.bot.handlers.audio import handle_audio, handle_voice


@pytest.fixture
def audio_message():
    """Create a mock audio message."""
    message = AsyncMock(spec=Message)
    message.from_user = User(id=123456789, is_bot=False, first_name="Test")
    message.chat = Chat(id=123456789, type="private")
    message.audio = Audio(
        file_id="test_file_id",
        file_unique_id="test_unique_id",
        duration=60,
        file_name="test.mp3",
        mime_type="audio/mp3",
        file_size=1024 * 1024  # 1 MB
    )
    return message


@pytest.fixture
def voice_message():
    """Create a mock voice message."""
    message = AsyncMock(spec=Message)
    message.from_user = User(id=123456789, is_bot=False, first_name="Test")
    message.chat = Chat(id=123456789, type="private")
    message.voice = Voice(
        file_id="test_file_id",
        file_unique_id="test_unique_id",
        duration=60,
        mime_type="audio/ogg",
        file_size=1024 * 1024  # 1 MB
    )
    return message


async def test_handle_audio(audio_message, dialog_manager):
    """Test the audio handler."""
    audio_service = AsyncMock()
    await handle_audio(audio_message, dialog_manager, audio_service)
    audio_message.answer.assert_called_once()
    dialog_manager.start.assert_called_once()


async def test_handle_voice(voice_message, dialog_manager):
    """Test the voice handler."""
    audio_service = AsyncMock()
    await handle_voice(voice_message, dialog_manager, audio_service)
    voice_message.answer.assert_called_once()
    dialog_manager.start.assert_called_once()
```

#### Критерии для ручного тестирования

1. **Проверка команд:**
   - Отправьте команду /start и убедитесь, что бот отвечает приветствием
   - Отправьте команду /help и проверьте, что открывается диалог справки
   - Отправьте команду /settings и убедитесь, что открывается диалог настроек

2. **Проверка диалогов:**
   - В диалоге настроек проверьте, что можно выбрать модель и формат экспорта
   - Убедитесь, что кнопки в диалогах работают корректно
   - Проверьте, что данные в диалогах обновляются при изменении настроек

3. **Проверка обработки файлов:**
   - Отправьте аудиофайл и убедитесь, что бот начинает его обработку
   - Отправьте голосовое сообщение и проверьте, что бот корректно его принимает
   - Попробуйте отправить файл большого размера и убедитесь, что бот выдает ошибку

4. **Проверка обработки ошибок:**
   - Вызовите ошибку в боте и убедитесь, что она корректно обрабатывается
   - Проверьте, что ошибки логируются в структурированном формате
   - Убедитесь, что пользователь получает понятное сообщение об ошибке

## Вопросы к постановщику задачи
1. Какие дополнительные команды нужно реализовать в боте?
2. Требуется ли поддержка групповых чатов или бот будет работать только в личных сообщениях?
3. Какие конкретные метрики использования бота нужно отслеживать?
4. Требуется ли реализация механизма ограничения доступа к боту (белый список пользователей)?
5. Какие дополнительные интерактивные элементы нужно добавить в диалоги?