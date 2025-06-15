# Фаза 3, День 14: Обработка ошибок: User-friendly сообщения, retry логика

## Цель (Definition of Done)
- Реализована система пользовательских сообщений об ошибках с понятными объяснениями
- Внедрена автоматическая retry логика для обработки временных сбоев
- Добавлены интерактивные механизмы для пользовательских повторных попыток
- Реализована система рекомендаций по исправлению ошибок
- Настроено логирование пользовательских действий при возникновении ошибок
- Добавлены метрики для отслеживания частоты и типов ошибок

## Ссылки на документацию
- [aiogram 3.x Documentation](https://docs.aiogram.dev/en/latest/)
- [aiogram-dialog Documentation](https://github.com/Tishka17/aiogram_dialog)
- [Structlog Documentation](https://www.structlog.org/en/stable/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Prometheus Client Documentation](https://github.com/prometheus/client_python)
- [Exponential Backoff Algorithm](https://en.wikipedia.org/wiki/Exponential_backoff)

---

## 1. Техническая секция

### Описание
В этом разделе мы улучшим пользовательский опыт при возникновении ошибок, реализовав понятные сообщения и механизмы автоматического восстановления. Основные компоненты включают:

1. **User-friendly сообщения об ошибках**: Преобразование технических ошибок в понятные пользователю сообщения
2. **Автоматическая retry логика**: Механизмы повторных попыток для временных сбоев
3. **Интерактивные механизмы восстановления**: Предоставление пользователю возможности исправить ошибку или повторить операцию
4. **Рекомендации по исправлению**: Конкретные советы по устранению проблем
5. **Метрики ошибок**: Сбор и анализ данных о частоте и типах ошибок

### Примеры кода

#### Преобразование технических ошибок в пользовательские сообщения

```python
# src/bot/error_messages.py
from typing import Dict, Any, Optional, Tuple
import re

from src.infrastructure.exceptions.base import (
    AppException, ValidationException, NotFoundException, 
    UnauthorizedException, ForbiddenException, ServiceUnavailableException
)
from src.domains.audio.exceptions import (
    AudioProcessingException, UnsupportedAudioFormatException, AudioTooLargeException
)
from src.domains.transcription.exceptions import (
    TranscriptionException, ModelLoadingException, TranscriptionTimeoutException
)
from src.domains.diarization.exceptions import (
    DiarizationException, TooManySpeakersException
)

class UserFriendlyError:
    """Class for user-friendly error messages."""
    
    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        can_retry: bool = False,
        retry_message: Optional[str] = None,
        error_code: Optional[str] = None,
    ):
        self.message = message
        self.suggestion = suggestion
        self.can_retry = can_retry
        self.retry_message = retry_message or "Попробовать снова"
        self.error_code = error_code
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message": self.message,
            "suggestion": self.suggestion,
            "can_retry": self.can_retry,
            "retry_message": self.retry_message,
            "error_code": self.error_code,
        }
    
    def __str__(self) -> str:
        """String representation."""
        result = f"❌ {self.message}"
        if self.suggestion:
            result += f"\n\n💡 {self.suggestion}"
        return result

def get_user_friendly_error(exception: Exception) -> UserFriendlyError:
    """Convert exception to user-friendly error message."""
    
    # Handle specific exceptions
    if isinstance(exception, UnsupportedAudioFormatException):
        supported_formats = exception.details.get("supported_formats", ["mp3", "wav", "ogg", "m4a"])
        formats_str = ", ".join(supported_formats)
        return UserFriendlyError(
            message=f"Формат аудио не поддерживается.",
            suggestion=f"Пожалуйста, отправьте файл в одном из следующих форматов: {formats_str}.",
            can_retry=True,
            error_code="unsupported_format"
        )
    
    elif isinstance(exception, AudioTooLargeException):
        max_size = exception.details.get("max_size", 200 * 1024 * 1024)  # Default 200MB
        max_size_mb = max_size / (1024 * 1024)
        return UserFriendlyError(
            message=f"Аудиофайл слишком большой.",
            suggestion=f"Максимальный размер файла: {max_size_mb:.0f}MB. Пожалуйста, отправьте файл меньшего размера или разделите его на части.",
            can_retry=True,
            error_code="file_too_large"
        )
    
    elif isinstance(exception, ModelLoadingException):
        return UserFriendlyError(
            message="Не удалось загрузить модель для транскрипции.",
            suggestion="Наши серверы сейчас перегружены. Пожалуйста, попробуйте позже или выберите другую модель в настройках.",
            can_retry=True,
            retry_message="Попробовать с другой моделью",
            error_code="model_loading_error"
        )
    
    elif isinstance(exception, TranscriptionTimeoutException):
        return UserFriendlyError(
            message="Время обработки аудио истекло.",
            suggestion="Файл слишком длинный или сервер перегружен. Попробуйте разделить файл на части или выбрать более быструю модель в настройках.",
            can_retry=True,
            retry_message="Попробовать с другой моделью",
            error_code="transcription_timeout"
        )
    
    elif isinstance(exception, TooManySpeakersException):
        return UserFriendlyError(
            message="Обнаружено слишком много говорящих.",
            suggestion="Система может корректно разделить до 10 говорящих. Попробуйте разделить аудио на части с меньшим количеством участников.",
            can_retry=True,
            error_code="too_many_speakers"
        )
    
    elif isinstance(exception, ServiceUnavailableException):
        service_name = exception.details.get("service", "Сервис")
        retry_after = exception.details.get("retry_after", 60)
        retry_after_min = max(1, int(retry_after / 60))
        
        return UserFriendlyError(
            message=f"{service_name} временно недоступен.",
            suggestion=f"Пожалуйста, повторите попытку через {retry_after_min} мин. Мы работаем над восстановлением сервиса.",
            can_retry=True,
            error_code="service_unavailable"
        )
    
    elif isinstance(exception, ValidationException):
        field_errors = exception.field_errors
        if field_errors and len(field_errors) > 0:
            fields = ", ".join([error.get("field", "") for error in field_errors])
            return UserFriendlyError(
                message="Некорректные данные.",
                suggestion=f"Пожалуйста, проверьте следующие поля: {fields}.",
                can_retry=True,
                error_code="validation_error"
            )
        return UserFriendlyError(
            message="Некорректные данные.",
            suggestion="Пожалуйста, проверьте введенные данные и попробуйте снова.",
            can_retry=True,
            error_code="validation_error"
        )
    
    elif isinstance(exception, NotFoundException):
        resource_type = exception.details.get("resource_type", "Ресурс")
        return UserFriendlyError(
            message=f"{resource_type} не найден.",
            suggestion="Возможно, ресурс был удален или у вас нет к нему доступа.",
            can_retry=False,
            error_code="not_found"
        )
    
    elif isinstance(exception, UnauthorizedException):
        return UserFriendlyError(
            message="Требуется авторизация.",
            suggestion="Пожалуйста, перезапустите бота командой /start.",
            can_retry=False,
            error_code="unauthorized"
        )
    
    elif isinstance(exception, ForbiddenException):
        return UserFriendlyError(
            message="Доступ запрещен.",
            suggestion="У вас нет прав для выполнения этой операции.",
            can_retry=False,
            error_code="forbidden"
        )
    
    elif isinstance(exception, AudioProcessingException):
        return UserFriendlyError(
            message="Ошибка обработки аудио.",
            suggestion="Возможно, файл поврежден. Попробуйте отправить другой файл или конвертировать его в другой формат.",
            can_retry=True,
            error_code="audio_processing_error"
        )
    
    elif isinstance(exception, TranscriptionException):
        return UserFriendlyError(
            message="Ошибка транскрипции.",
            suggestion="Произошла ошибка при обработке аудио. Пожалуйста, попробуйте позже или используйте другую модель.",
            can_retry=True,
            retry_message="Попробовать с другой моделью",
            error_code="transcription_error"
        )
    
    elif isinstance(exception, DiarizationException):
        return UserFriendlyError(
            message="Ошибка разделения по говорящим.",
            suggestion="Попробуйте отключить диаризацию в настройках или использовать аудио с лучшим качеством звука.",
            can_retry=True,
            retry_message="Попробовать без диаризации",
            error_code="diarization_error"
        )
    
    elif isinstance(exception, AppException):
        return UserFriendlyError(
            message=exception.message,
            suggestion="Пожалуйста, попробуйте позже или обратитесь в поддержку.",
            can_retry=True,
            error_code=exception.code
        )
    
    # Generic error handler
    return UserFriendlyError(
        message="Произошла непредвиденная ошибка.",
        suggestion="Пожалуйста, попробуйте позже или обратитесь в поддержку.",
        can_retry=True,
        error_code="unknown_error"
    )
```

#### Интеграция с диалогами для отображения ошибок

```python
# src/bot/dialogs/error_dialog.py
from typing import Any, Dict, Optional
import asyncio

from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, Cancel
from aiogram_dialog.widgets.text import Const, Format

from src.bot.states import ErrorState, MainMenuState
from src.bot.error_messages import UserFriendlyError

async def error_getter(dialog_manager: DialogManager, **kwargs):
    """Get error information."""
    error = dialog_manager.dialog_data.get("error")
    if not error:
        return {
            "message": "Произошла неизвестная ошибка.",
            "suggestion": "Пожалуйста, попробуйте позже или обратитесь в поддержку.",
            "can_retry": False,
            "retry_message": "Попробовать снова",
            "error_code": "unknown_error"
        }
    
    return error.to_dict() if isinstance(error, UserFriendlyError) else error

async def on_retry(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Handler for retry button."""
    # Get retry state and data
    retry_state = dialog_manager.dialog_data.get("retry_state")
    retry_data = dialog_manager.dialog_data.get("retry_data", {})
    
    if retry_state:
        # Start the retry state with data
        await dialog_manager.start(retry_state, data=retry_data)
    else:
        # Fallback to main menu
        await dialog_manager.start(MainMenuState.main)

async def on_settings(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Handler for settings button."""
    from src.bot.states import SettingsState
    await dialog_manager.start(SettingsState.main)

async def on_support(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Handler for support button."""
    # Send support message
    await callback.message.answer(
        "Для получения поддержки, пожалуйста, напишите нам: @support_username\n"
        "Укажите код ошибки: " + dialog_manager.dialog_data.get("error", {}).get("error_code", "unknown")
    )
    
    # Go back to main menu
    await dialog_manager.start(MainMenuState.main)

# Error window
error_window = Window(
    Format("{message}"),
    Format("\n\n💡 {suggestion}", when=F.data["suggestion"]),
    Row(
        Button(
            Format("{retry_message}"),
            id="retry",
            on_click=on_retry,
            when=F.data["can_retry"]
        ),
    ),
    Row(
        Button(
            Const("⚙️ Настройки"),
            id="settings",
            on_click=on_settings,
        ),
        Button(
            Const("🆘 Поддержка"),
            id="support",
            on_click=on_support,
        ),
    ),
    Row(
        Cancel(Const("🔙 Назад"))
    ),
    state=ErrorState.show,
    getter=error_getter
)

# Create dialog
error_dialog = Dialog(error_window)
```

#### Обновление прогресс-диалога с обработкой ошибок

```python
# src/bot/dialogs/progress.py
# Обновленная версия с улучшенной обработкой ошибок

from typing import Any, Dict
import asyncio
import structlog

from aiogram import F
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, Cancel
from aiogram_dialog.widgets.text import Const, Format

from src.bot.states import ProgressState, MainMenuState, ErrorState
from src.domains.transcription.services import TranscriptionService
from src.bot.error_messages import get_user_friendly_error

logger = structlog.get_logger()

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
    
    try:
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
            
            # If failed, store error in dialog data
            if is_failed:
                error = task_status.get("error")
                if error:
                    # Convert to user-friendly error
                    user_error = get_user_friendly_error(error)
                    dialog_manager.dialog_data["error"] = user_error
        
        return {
            "progress": int(progress * 100),
            "status": task_status.get("status_message", "Обработка..."),
            "progress_bar": progress_bar,
            "is_completed": is_completed,
            "is_failed": is_failed,
            "error_message": task_status.get("error_message", "")
        }
    except Exception as e:
        logger.exception("Error getting task status", task_id=task_id, error=str(e))
        dialog_manager.dialog_data["stop_polling"] = True
        dialog_manager.dialog_data["error"] = get_user_friendly_error(e)
        
        return {
            "progress": 0,
            "status": "Ошибка получения статуса",
            "progress_bar": "⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜",
            "is_completed": False,
            "is_failed": True,
            "error_message": str(e)
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
        try:
            await transcription_service.cancel_task(task_id)
        except Exception as e:
            logger.exception("Error canceling task", task_id=task_id, error=str(e))
    
    # Go back to main menu
    await dialog_manager.start(MainMenuState.main)

async def on_error_details(callback: CallbackQuery, button: Button, 
                          dialog_manager: DialogManager):
    """Handler for showing error details."""
    error = dialog_manager.dialog_data.get("error")
    if error:
        # Store retry information
        dialog_manager.dialog_data["retry_state"] = dialog_manager.dialog_data.get("retry_state", MainMenuState.main)
        dialog_manager.dialog_data["retry_data"] = dialog_manager.dialog_data.get("retry_data", {})
        
        # Show error dialog
        await dialog_manager.start(ErrorState.show)
    else:
        # Fallback to main menu
        await dialog_manager.start(MainMenuState.main)

async def on_dialog_started(start_data: Dict[str, Any], manager: DialogManager):
    """Called when dialog is started."""
    # Store task_id in dialog data
    if start_data and "task_id" in start_data:
        manager.dialog_data["task_id"] = start_data["task_id"]
    
    # Store retry information if provided
    if start_data and "retry_state" in start_data:
        manager.dialog_data["retry_state"] = start_data["retry_state"]
    if start_data and "retry_data" in start_data:
        manager.dialog_data["retry_data"] = start_data["retry_data"]
    
    # Start polling for progress updates
    manager.dialog_data["stop_polling"] = False
    asyncio.create_task(poll_progress(manager))

async def poll_progress(manager: DialogManager):
    """Poll for progress updates."""
    try:
        while not manager.dialog_data.get("stop_polling", False):
            await manager.update({})  # Trigger getter to update progress
            await asyncio.sleep(1)  # Poll every second
    except Exception as e:
        logger.exception("Error in progress polling", error=str(e))
        manager.dialog_data["stop_polling"] = True
        manager.dialog_data["error"] = get_user_friendly_error(e)
        await manager.update({})

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
            Const("❓ Подробнее об ошибке"),
            id="error_details",
            on_click=on_error_details,
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

#### Обновление сервиса транскрипции с retry логикой

```python
# src/domains/transcription/services.py
from typing import Dict, Any, Optional, List
import asyncio
import time
import random
import structlog
from prometheus_client import Counter, Histogram

from src.infrastructure.exceptions.base import AppException, ServiceUnavailableException
from src.infrastructure.resilience.retry import with_retry
from src.infrastructure.resilience.circuit_breaker import with_circuit_breaker
from src.domains.transcription.exceptions import (
    TranscriptionException, ModelLoadingException, TranscriptionTimeoutException
)

logger = structlog.get_logger()

# Metrics
TRANSCRIPTION_ERRORS = Counter(
    'transcription_errors_total',
    'Total number of transcription errors',
    ['error_type', 'model']
)

TRANSCRIPTION_RETRIES = Counter(
    'transcription_retries_total',
    'Total number of transcription retries',
    ['model']
)

TRANSCRIPTION_DURATION = Histogram(
    'transcription_duration_seconds',
    'Transcription duration in seconds',
    ['model', 'status']
)

class TranscriptionService:
    """Service for transcription operations."""
    
    def __init__(self):
        """Initialize service."""
        # Dependencies would be injected here
        pass
    
    @with_retry(
        max_retries=3,
        initial_delay=1.0,
        max_delay=10.0,
        backoff_factor=2.0,
        jitter=True,
        retry_exceptions=[ServiceUnavailableException, ConnectionError, TimeoutError]
    )
    @with_circuit_breaker(
        name="transcription_service",
        failure_threshold=5,
        recovery_timeout=30.0,
        expected_exceptions=[ServiceUnavailableException, ConnectionError, TimeoutError]
    )
    async def create_transcription_task(
        self,
        file_id: str,
        user_id: int,
        model: str = "whisper-large-v3",
        language: str = "auto",
        diarization: bool = True
    ) -> str:
        """Create a transcription task."""
        # Implementation would call the actual service
        # This is a simplified example
        
        try:
            # Log task creation
            logger.info(
                "Creating transcription task",
                file_id=file_id,
                user_id=user_id,
                model=model,
                language=language,
                diarization=diarization
            )
            
            # Call the actual service
            # ...
            
            # Return task ID
            return f"task-{int(time.time())}-{random.randint(1000, 9999)}"
        
        except Exception as e:
            # Log error
            logger.exception(
                "Error creating transcription task",
                file_id=file_id,
                user_id=user_id,
                model=model,
                error=str(e)
            )
            
            # Increment error metric
            TRANSCRIPTION_ERRORS.labels(
                error_type=e.__class__.__name__,
                model=model
            ).inc()
            
            # Re-raise as domain exception
            if isinstance(e, AppException):
                raise
            
            raise TranscriptionException(
                message="Error creating transcription task",
                details={"original_error": str(e)},
                task_id=None
            )
    
    @with_retry(
        max_retries=5,
        initial_delay=0.5,
        max_delay=5.0,
        backoff_factor=1.5,
        jitter=True,
        retry_exceptions=[ConnectionError, TimeoutError]
    )
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status."""
        # Implementation would call the actual service
        # This is a simplified example
        
        try:
            # Call the actual service
            # ...
            
            # Return status
            return {
                "task_id": task_id,
                "progress": 0.5,  # Example progress
                "status": "processing",
                "status_message": "Обработка аудио...",
            }
        
        except Exception as e:
            logger.exception(
                "Error getting task status",
                task_id=task_id,
                error=str(e)
            )
            
            # Return error status
            return {
                "task_id": task_id,
                "progress": 0,
                "status": "failed",
                "status_message": "Ошибка получения статуса",
                "error_message": str(e),
                "error": e
            }
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        # Implementation would call the actual service
        # This is a simplified example
        
        try:
            # Log cancellation
            logger.info("Canceling task", task_id=task_id)
            
            # Call the actual service
            # ...
            
            return True
        
        except Exception as e:
            logger.exception(
                "Error canceling task",
                task_id=task_id,
                error=str(e)
            )
            
            # Re-raise as domain exception
            if isinstance(e, AppException):
                raise
            
            raise TranscriptionException(
                message="Error canceling task",
                details={"original_error": str(e)},
                task_id=task_id
            )
    
    async def retry_task(self, task_id: str, new_params: Optional[Dict[str, Any]] = None) -> str:
        """Retry a failed task with optional new parameters."""
        try:
            # Get original task details
            task_details = await self.get_task_details(task_id)
            if not task_details:
                raise TranscriptionException(
                    message="Task not found",
                    task_id=task_id
                )
            
            # Merge original parameters with new ones
            params = {
                "file_id": task_details.get("file_id"),
                "user_id": task_details.get("user_id"),
                "model": task_details.get("model", "whisper-large-v3"),
                "language": task_details.get("language", "auto"),
                "diarization": task_details.get("diarization", True)
            }
            
            if new_params:
                params.update(new_params)
            
            # Increment retry metric
            TRANSCRIPTION_RETRIES.labels(
                model=params.get("model")
            ).inc()
            
            # Create new task
            return await self.create_transcription_task(**params)
        
        except Exception as e:
            logger.exception(
                "Error retrying task",
                task_id=task_id,
                error=str(e)
            )
            
            # Re-raise as domain exception
            if isinstance(e, AppException):
                raise
            
            raise TranscriptionException(
                message="Error retrying task",
                details={"original_error": str(e)},
                task_id=task_id
            )
    
    async def get_task_details(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a task."""
        # Implementation would call the actual service
        # This is a simplified example
        
        try:
            # Call the actual service
            # ...
            
            # Return details
            return {
                "id": task_id,
                "file_id": "file-123",
                "user_id": 123456,
                "file_name": "audio.mp3",
                "file_size": 1024 * 1024,  # 1MB
                "duration": 60,  # 1 minute
                "model": "whisper-large-v3",
                "language": "auto",
                "diarization": True,
                "status": "completed",
                "created_at": time.time(),
                "speakers_count": 2
            }
        
        except Exception as e:
            logger.exception(
                "Error getting task details",
                task_id=task_id,
                error=str(e)
            )
            
            return None
```

#### Обновление обработчика команд с обработкой ошибок

```python
# src/bot/handlers/commands.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram_dialog import DialogManager
import structlog

from src.bot.states import MainMenuState, ErrorState
from src.bot.error_messages import get_user_friendly_error, UserFriendlyError

logger = structlog.get_logger()

def register_command_handlers(router: Router):
    """Register command handlers."""
    
    @router.message(Command("start"))
    async def cmd_start(message: Message, dialog_manager: DialogManager):
        """Handler for /start command."""
        try:
            # Start main menu dialog
            await dialog_manager.start(MainMenuState.main)
        except Exception as e:
            logger.exception("Error in start command", error=str(e), user_id=message.from_user.id)
            
            # Convert to user-friendly error
            error = get_user_friendly_error(e)
            
            # Show error message
            await message.answer(str(error))
    
    @router.message(Command("help"))
    async def cmd_help(message: Message):
        """Handler for /help command."""
        help_text = (
            "🤖 *Transcription Bot* помогает транскрибировать аудио в текст.\n\n"
            "Основные команды:\n"
            "/start - Запустить бота\n"
            "/help - Показать эту справку\n"
            "/settings - Настройки транскрипции\n"
            "/history - История транскрипций\n\n"
            "Для начала работы, просто отправьте аудиофайл или голосовое сообщение."
        )
        
        await message.answer(help_text, parse_mode="Markdown")
    
    @router.message(Command("settings"))
    async def cmd_settings(message: Message, dialog_manager: DialogManager):
        """Handler for /settings command."""
        try:
            from src.bot.states import SettingsState
            await dialog_manager.start(SettingsState.main)
        except Exception as e:
            logger.exception("Error in settings command", error=str(e), user_id=message.from_user.id)
            
            # Convert to user-friendly error
            error = get_user_friendly_error(e)
            
            # Show error message
            await message.answer(str(error))
    
    @router.message(Command("history"))
    async def cmd_history(message: Message, dialog_manager: DialogManager):
        """Handler for /history command."""
        try:
            from src.bot.states import HistoryState
            await dialog_manager.start(HistoryState.list)
        except Exception as e:
            logger.exception("Error in history command", error=str(e), user_id=message.from_user.id)
            
            # Convert to user-friendly error
            error = get_user_friendly_error(e)
            
            # Show error message
            await message.answer(str(error))
    
    @router.message(Command("cancel"))
    async def cmd_cancel(message: Message, dialog_manager: DialogManager):
        """Handler for /cancel command."""
        try:
            # Check if there's an active dialog
            if dialog_manager.has_context():
                await dialog_manager.done()
            
            # Go to main menu
            await dialog_manager.start(MainMenuState.main)
        except Exception as e:
            logger.exception("Error in cancel command", error=str(e), user_id=message.from_user.id)
            
            # Convert to user-friendly error
            error = get_user_friendly_error(e)
            
            # Show error message
            await message.answer(str(error))
    
    @router.error()
    async def error_handler(event_from_user, exception, dialog_manager: DialogManager):
        """Global error handler."""
        try:
            logger.exception(
                "Unhandled exception in handler",
                error=str(exception),
                user_id=event_from_user.id if hasattr(event_from_user, 'id') else None
            )
            
            # Convert to user-friendly error
            error = get_user_friendly_error(exception)
            
            # Store error in dialog data
            dialog_manager.dialog_data["error"] = error
            
            # Show error dialog
            await dialog_manager.start(ErrorState.show)
        except Exception as e:
            logger.exception("Error in error handler", error=str(e))
            
            # Fallback to simple message
            if hasattr(event_from_user, 'answer'):
                await event_from_user.answer(
                    "❌ Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже или обратитесь в поддержку."
                )
```

#### Обновление состояний для включения диалога ошибок

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

class ErrorState(StatesGroup):
    """Error handling states."""
    show = State()
```

#### Метрики для отслеживания ошибок

```python
# src/infrastructure/monitoring/error_metrics.py
from prometheus_client import Counter, Histogram, Gauge
import structlog

logger = structlog.get_logger()

# Define metrics
ERROR_COUNTER = Counter(
    'app_errors_total',
    'Total number of errors',
    ['error_type', 'error_code', 'component']
)

ERROR_RETRY_COUNTER = Counter(
    'app_error_retries_total',
    'Total number of error retries',
    ['error_type', 'error_code', 'component']
)

USER_ERROR_COUNTER = Counter(
    'app_user_errors_total',
    'Total number of user-facing errors',
    ['error_code', 'can_retry']
)

ERROR_DURATION = Histogram(
    'app_error_resolution_duration_seconds',
    'Time taken to resolve errors',
    ['error_type', 'resolution_type']
)

ACTIVE_ERRORS = Gauge(
    'app_active_errors',
    'Number of active errors',
    ['component']
)

def track_error(error_type: str, error_code: str, component: str):
    """Track an error occurrence."""
    ERROR_COUNTER.labels(
        error_type=error_type,
        error_code=error_code,
        component=component
    ).inc()
    
    ACTIVE_ERRORS.labels(component=component).inc()
    
    logger.info(
        "Error tracked",
        error_type=error_type,
        error_code=error_code,
        component=component
    )

def track_error_resolution(error_type: str, resolution_type: str, duration_seconds: float):
    """Track error resolution time."""
    ERROR_DURATION.labels(
        error_type=error_type,
        resolution_type=resolution_type
    ).observe(duration_seconds)
    
    logger.info(
        "Error resolved",
        error_type=error_type,
        resolution_type=resolution_type,
        duration_seconds=duration_seconds
    )

def track_error_retry(error_type: str, error_code: str, component: str):
    """Track an error retry."""
    ERROR_RETRY_COUNTER.labels(
        error_type=error_type,
        error_code=error_code,
        component=component
    ).inc()
    
    logger.info(
        "Error retry",
        error_type=error_type,
        error_code=error_code,
        component=component
    )

def track_user_error(error_code: str, can_retry: bool):
    """Track a user-facing error."""
    USER_ERROR_COUNTER.labels(
        error_code=error_code,
        can_retry=str(can_retry)
    ).inc()
    
    logger.info(
        "User error",
        error_code=error_code,
        can_retry=can_retry
    )

def clear_active_error(component: str):
    """Clear an active error."""
    ACTIVE_ERRORS.labels(component=component).dec()
    
    logger.info(
        "Active error cleared",
        component=component
    )
```

### Конфигурации

#### Обновление регистрации диалогов

```python
# src/bot/dialogs/registry.py
from aiogram_dialog import DialogRegistry
from aiogram.dispatcher.router import Router

from src.bot.dialogs.main_menu import main_menu_dialog
from src.bot.dialogs.transcription import transcription_dialog
from src.bot.dialogs.settings import settings_dialog
from src.bot.dialogs.history import history_dialog
from src.bot.dialogs.progress import progress_dialog
from src.bot.dialogs.error_dialog import error_dialog

def setup_dialogs(router: Router) -> DialogRegistry:
    """Register all dialogs in the registry."""
    registry = DialogRegistry(router)
    
    # Register dialogs
    registry.register(main_menu_dialog)
    registry.register(transcription_dialog)
    registry.register(settings_dialog)
    registry.register(history_dialog)
    registry.register(progress_dialog)
    registry.register(error_dialog)  # Add error dialog
    
    return registry
```

#### Настройка логирования ошибок

```python
# src/infrastructure/logging/error_logging.py
import structlog
from typing import Dict, Any, Optional
import traceback
import json
import time

from src.infrastructure.monitoring.error_metrics import track_error

def log_error(
    logger: structlog.BoundLogger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    component: str = "unknown",
):
    """Log an error with context."""
    # Create error context
    error_context = {
        "error_type": error.__class__.__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "timestamp": time.time(),
        "component": component,
    }
    
    # Add user context if available
    if user_id:
        error_context["user_id"] = user_id
    
    # Add additional context
    if context:
        error_context.update(context)
    
    # Log the error
    logger.error("Error occurred", **error_context)
    
    # Track in metrics
    error_code = getattr(error, "code", "unknown")
    track_error(
        error_type=error.__class__.__name__,
        error_code=error_code,
        component=component
    )
    
    return error_context
```

### Схемы данных/API

#### Схемы для ошибок

```python
# src/api/schemas/errors.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ErrorDetail(BaseModel):
    """Model for detailed error information."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class ErrorResponse(BaseModel):
    """Model for error responses."""
    error: ErrorDetail = Field(..., description="Error details")

class FieldError(BaseModel):
    """Model for field validation errors."""
    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")

class ValidationErrorResponse(ErrorResponse):
    """Model for validation error responses."""
    field_errors: List[FieldError] = Field([], description="Field-specific errors")

class UserFriendlyErrorResponse(BaseModel):
    """Model for user-friendly error responses."""
    message: str = Field(..., description="User-friendly error message")
    suggestion: Optional[str] = Field(None, description="Suggestion for resolving the error")
    can_retry: bool = Field(False, description="Whether the operation can be retried")
    retry_message: Optional[str] = Field(None, description="Message for retry button")
    error_code: Optional[str] = Field(None, description="Error code for reference")
```

## 2. Практическая секция

### Пошаговые инструкции

1. **Создание системы пользовательских сообщений об ошибках**
   - Создайте модуль `src/bot/error_messages.py`
   - Реализуйте класс `UserFriendlyError` для представления ошибок в понятном пользователю формате
   - Добавьте функцию `get_user_friendly_error` для преобразования технических исключений в пользовательские сообщения
   - Настройте сообщения для всех типов ошибок, которые могут возникнуть в приложении

2. **Реализация диалога для отображения ошибок**
   - Добавьте новое состояние `ErrorState` в `src/bot/states.py`
   - Создайте модуль `src/bot/dialogs/error_dialog.py`
   - Реализуйте диалог с информацией об ошибке, предложениями по исправлению и кнопками действий
   - Добавьте возможность повторной попытки, перехода к настройкам или обращения в поддержку

3. **Обновление прогресс-диалога с улучшенной обработкой ошибок**
   - Обновите `src/bot/dialogs/progress.py` для использования пользовательских сообщений об ошибках
   - Добавьте кнопку для просмотра подробностей об ошибке
   - Реализуйте механизм сохранения контекста для возможности повторной попытки

4. **Внедрение retry логики в сервисы**
   - Обновите `src/domains/transcription/services.py` с использованием декораторов `@with_retry` и `@with_circuit_breaker`
   - Добавьте метод `retry_task` для повторного запуска задачи с новыми параметрами
   - Реализуйте логирование и метрики для отслеживания повторных попыток

5. **Обновление обработчиков команд с обработкой ошибок**
   - Обновите `src/bot/handlers/commands.py` для обработки исключений во всех обработчиках
   - Добавьте глобальный обработчик ошибок `error_handler`
   - Реализуйте преобразование исключений в пользовательские сообщения

6. **Настройка метрик для отслеживания ошибок**
   - Создайте модуль `src/infrastructure/monitoring/error_metrics.py`
   - Добавьте метрики для подсчета ошибок, повторных попыток и времени разрешения
   - Реализуйте функции для трекинга ошибок и их разрешения

7. **Улучшение логирования ошибок**
   - Создайте модуль `src/infrastructure/logging/error_logging.py`
   - Реализуйте функцию `log_error` для логирования ошибок с контекстом
   - Интегрируйте логирование с системой метрик

8. **Обновление регистрации диалогов**
   - Обновите `src/bot/dialogs/registry.py` для включения диалога ошибок
   - Проверьте корректность регистрации всех диалогов

### Частые ошибки (Common Pitfalls)

1. **Слишком технические сообщения об ошибках**
   - Избегайте технических терминов в сообщениях для пользователей
   - Не включайте трассировки стека или коды ошибок в сообщения
   - Используйте понятный язык и предлагайте конкретные действия

2. **Недостаточная информация для отладки**
   - Всегда логируйте технические детали ошибок для отладки
   - Сохраняйте контекст ошибки (пользователь, действие, параметры)
   - Используйте уникальные идентификаторы для связывания пользовательских ошибок с логами

3. **Бесконечные повторные попытки**
   - Устанавливайте разумные ограничения на количество повторных попыток
   - Используйте экспоненциальную задержку между попытками
   - Реализуйте механизм Circuit Breaker для предотвращения каскадных сбоев

4. **Игнорирование ошибок в асинхронных задачах**
   - Всегда обрабатывайте исключения в асинхронных функциях
   - Используйте `try/except` внутри `asyncio.create_task()`
   - Логируйте ошибки в фоновых задачах

5. **Отсутствие метрик для анализа ошибок**
   - Собирайте метрики о частоте и типах ошибок
   - Отслеживайте успешность повторных попыток
   - Анализируйте тренды для выявления системных проблем

### Советы по оптимизации (Performance Tips)

1. **Оптимизация retry логики**
   - Используйте разные параметры retry для разных типов ошибок
   - Применяйте jitter для предотвращения "thundering herd" проблемы
   - Кешируйте результаты промежуточных шагов для ускорения повторных попыток

2. **Эффективное логирование ошибок**
   - Используйте структурированное логирование для удобного анализа
   - Логируйте только необходимую информацию для отладки
   - Применяйте разные уровни логирования для разных типов ошибок

3. **Оптимизация отображения ошибок**
   - Группируйте похожие ошибки для уменьшения шума
   - Предлагайте наиболее вероятные решения проблем
   - Используйте контекст пользователя для персонализации сообщений

4. **Кеширование сообщений об ошибках**
   - Кешируйте часто используемые сообщения об ошибках
   - Предварительно загружайте шаблоны сообщений
   - Используйте локализацию для многоязычных сообщений

5. **Мониторинг и алерты**
   - Настройте алерты на аномальное количество ошибок
   - Отслеживайте время восстановления после сбоев
   - Анализируйте корреляции между ошибками и другими метриками

## 3. Валидационная секция

### Чек-лист для самопроверки

- [ ] Реализована система пользовательских сообщений об ошибках
- [ ] Создан диалог для отображения ошибок с возможностью повторной попытки
- [ ] Обновлен прогресс-диалог с улучшенной обработкой ошибок
- [ ] Внедрена retry логика в сервисы с использованием декораторов
- [ ] Обновлены обработчики команд с обработкой исключений
- [ ] Настроены метрики для отслеживания ошибок и повторных попыток
- [ ] Улучшено логирование ошибок с сохранением контекста
- [ ] Обновлена регистрация диалогов для включения диалога ошибок
- [ ] Добавлены пользовательские рекомендации по исправлению ошибок
- [ ] Реализована интеграция с системой мониторинга

### Автоматизированные тесты

```python
# tests/bot/test_error_messages.py
import pytest
from unittest.mock import MagicMock

from src.bot.error_messages import get_user_friendly_error, UserFriendlyError
from src.infrastructure.exceptions.base import AppException, ValidationException
from src.domains.audio.exceptions import UnsupportedAudioFormatException, AudioTooLargeException
from src.domains.transcription.exceptions import TranscriptionTimeoutException

def test_user_friendly_error_creation():
    """Test UserFriendlyError creation."""
    error = UserFriendlyError(
        message="Test error message",
        suggestion="Test suggestion",
        can_retry=True,
        retry_message="Try again",
        error_code="test_error"
    )
    
    assert error.message == "Test error message"
    assert error.suggestion == "Test suggestion"
    assert error.can_retry is True
    assert error.retry_message == "Try again"
    assert error.error_code == "test_error"
    
    # Test to_dict method
    error_dict = error.to_dict()
    assert error_dict["message"] == "Test error message"
    assert error_dict["suggestion"] == "Test suggestion"
    assert error_dict["can_retry"] is True
    assert error_dict["retry_message"] == "Try again"
    assert error_dict["error_code"] == "test_error"
    
    # Test string representation
    error_str = str(error)
    assert "❌ Test error message" in error_str
    assert "💡 Test suggestion" in error_str

def test_get_user_friendly_error_for_unsupported_format():
    """Test get_user_friendly_error for UnsupportedAudioFormatException."""
    exception = UnsupportedAudioFormatException(
        format="xyz",
        supported_formats=["mp3", "wav", "ogg"]
    )
    
    error = get_user_friendly_error(exception)
    
    assert isinstance(error, UserFriendlyError)
    assert "Формат аудио не поддерживается" in error.message
    assert "mp3, wav, ogg" in error.suggestion
    assert error.can_retry is True
    assert error.error_code == "unsupported_format"

def test_get_user_friendly_error_for_file_too_large():
    """Test get_user_friendly_error for AudioTooLargeException."""
    exception = AudioTooLargeException(
        file_size=300 * 1024 * 1024,  # 300MB
        max_size=200 * 1024 * 1024    # 200MB
    )
    
    error = get_user_friendly_error(exception)
    
    assert isinstance(error, UserFriendlyError)
    assert "Аудиофайл слишком большой" in error.message
    assert "200MB" in error.suggestion
    assert error.can_retry is True
    assert error.error_code == "file_too_large"

def test_get_user_friendly_error_for_timeout():
    """Test get_user_friendly_error for TranscriptionTimeoutException."""
    exception = TranscriptionTimeoutException(
        task_id="test-task",
        timeout=300  # 5 minutes
    )
    
    error = get_user_friendly_error(exception)
    
    assert isinstance(error, UserFriendlyError)
    assert "Время обработки аудио истекло" in error.message
    assert "разделить файл" in error.suggestion
    assert error.can_retry is True
    assert error.retry_message == "Попробовать с другой моделью"
    assert error.error_code == "transcription_timeout"

def test_get_user_friendly_error_for_validation():
    """Test get_user_friendly_error for ValidationException."""
    exception = ValidationException(
        field_errors=[
            {"field": "email", "message": "Invalid email format", "type": "value_error.email"},
            {"field": "name", "message": "Field required", "type": "value_error.missing"}
        ]
    )
    
    error = get_user_friendly_error(exception)
    
    assert isinstance(error, UserFriendlyError)
    assert "Некорректные данные" in error.message
    assert "email, name" in error.suggestion
    assert error.can_retry is True
    assert error.error_code == "validation_error"

def test_get_user_friendly_error_for_generic_exception():
    """Test get_user_friendly_error for generic Exception."""
    exception = Exception("Some random error")
    
    error = get_user_friendly_error(exception)
    
    assert isinstance(error, UserFriendlyError)
    assert "Произошла непредвиденная ошибка" in error.message
    assert "попробуйте позже" in error.suggestion
    assert error.can_retry is True
    assert error.error_code == "unknown_error"

# tests/bot/test_error_dialog.py
import pytest
from unittest.mock import AsyncMock, patch

from aiogram.types import CallbackQuery, User as TelegramUser
from aiogram_dialog import DialogManager

from src.bot.dialogs.error_dialog import error_getter, on_retry, on_settings, on_support
from src.bot.error_messages import UserFriendlyError
from src.bot.states import MainMenuState, SettingsState

@pytest.fixture
def dialog_manager():
    manager = AsyncMock(spec=DialogManager)
    manager.dialog_data = {}
    manager.start = AsyncMock()
    return manager

@pytest.fixture
def callback():
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = AsyncMock(spec=TelegramUser)
    callback.from_user.id = 123456
    return callback

async def test_error_getter_with_error(dialog_manager):
    """Test error_getter with error in dialog data."""
    error = UserFriendlyError(
        message="Test error",
        suggestion="Test suggestion",
        can_retry=True,
        error_code="test_error"
    )
    dialog_manager.dialog_data["error"] = error
    
    result = await error_getter(dialog_manager)
    
    assert result["message"] == "Test error"
    assert result["suggestion"] == "Test suggestion"
    assert result["can_retry"] is True
    assert result["error_code"] == "test_error"

async def test_error_getter_without_error(dialog_manager):
    """Test error_getter without error in dialog data."""
    result = await error_getter(dialog_manager)
    
    assert "message" in result
    assert "Произошла неизвестная ошибка" in result["message"]
    assert "suggestion" in result
    assert "error_code" in result
    assert result["error_code"] == "unknown_error"

async def test_on_retry_with_retry_state(dialog_manager, callback):
    """Test on_retry with retry state in dialog data."""
    dialog_manager.dialog_data["retry_state"] = MainMenuState.main
    dialog_manager.dialog_data["retry_data"] = {"key": "value"}
    
    await on_retry(callback, None, dialog_manager)
    
    dialog_manager.start.assert_called_once_with(MainMenuState.main, data={"key": "value"})

async def test_on_retry_without_retry_state(dialog_manager, callback):
    """Test on_retry without retry state in dialog data."""
    await on_retry(callback, None, dialog_manager)
    
    dialog_manager.start.assert_called_once_with(MainMenuState.main)

async def test_on_settings(dialog_manager, callback):
    """Test on_settings handler."""
    await on_settings(callback, None, dialog_manager)
    
    dialog_manager.start.assert_called_once_with(SettingsState.main)

async def test_on_support(dialog_manager, callback):
    """Test on_support handler."""
    dialog_manager.dialog_data["error"] = {"error_code": "test_error"}
    
    await on_support(callback, None, dialog_manager)
    
    callback.message.answer.assert_called_once()
    assert "test_error" in callback.message.answer.call_args[0][0]
    dialog_manager.start.assert_called_once_with(MainMenuState.main)
```

### Критерии для ручного тестирования

1. **Тестирование пользовательских сообщений об ошибках**
   - Вызовите различные типы ошибок (неподдерживаемый формат, большой файл, таймаут)
   - Проверьте, что сообщения понятны и содержат рекомендации по исправлению
   - Убедитесь, что технические детали ошибок не отображаются пользователю

2. **Тестирование диалога ошибок**
   - Проверьте отображение диалога при возникновении ошибки
   - Протестируйте кнопки действий (повторить, настройки, поддержка)
   - Убедитесь, что контекст сохраняется при повторной попытке

3. **Тестирование автоматических повторных попыток**
   - Вызовите временную ошибку (например, недоступность сервиса)
   - Проверьте, что система автоматически повторяет попытку
   - Убедитесь, что пользователь информируется о процессе повторных попыток

4. **Тестирование пользовательских повторных попыток**
   - Вызовите ошибку, которая требует действий пользователя
   - Проверьте возможность повторной попытки с измененными параметрами
   - Убедитесь, что новые параметры корректно применяются

5. **Тестирование метрик и логирования**
   - Вызовите различные типы ошибок и проверьте логи
   - Убедитесь, что метрики корректно обновляются
   - Проверьте, что контекст ошибок сохраняется в логах

6. **Тестирование обработки ошибок в командах**
   - Вызовите ошибки в различных командах (/start, /settings, /history)
   - Проверьте, что ошибки корректно обрабатываются
   - Убедитесь, что пользователь получает понятные сообщения

7. **Тестирование восстановления после сбоев**
   - Симулируйте сбой сервиса и проверьте механизм Circuit Breaker
   - Убедитесь, что система корректно восстанавливается после восстановления сервиса
   - Проверьте, что пользователь информируется о статусе восстановления

8. **Тестирование производительности**
   - Проверьте время отклика при обработке ошибок
   - Убедитесь, что повторные попытки не создают избыточной нагрузки
   - Проверьте работу системы при большом количестве одновременных ошибок