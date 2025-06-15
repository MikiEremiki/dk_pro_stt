# Фаза 2, День 9: Система задач: Taskiq/FastStream, мониторинг очередей

## Цель (Definition of Done)
- Реализована система асинхронной обработки задач с использованием Taskiq и FastStream
- Настроена очередь задач через NATS JetStream
- Реализован мониторинг очередей с метриками и алертами
- Система корректно обрабатывает длительные задачи транскрипции и диаризации
- Реализована возможность отслеживания прогресса выполнения задач

## Ссылки на документацию
- [Taskiq Documentation](https://taskiq-python.github.io/)
- [FastStream Documentation](https://faststream.airt.ai/latest/)
- [NATS JetStream Documentation](https://docs.nats.io/nats-concepts/jetstream)
- [Prometheus Client Python](https://github.com/prometheus/client_python)
- [Structlog Documentation](https://www.structlog.org/en/stable/)

---

## 1. Техническая секция

### Описание
Система задач является критическим компонентом нашего приложения, поскольку процессы транскрипции и диаризации могут занимать значительное время. Мы будем использовать Taskiq для управления асинхронными задачами и FastStream для работы с NATS JetStream в качестве брокера сообщений. Это позволит нам:

1. Асинхронно обрабатывать длительные задачи
2. Масштабировать обработку горизонтально
3. Отслеживать прогресс выполнения задач
4. Обеспечить отказоустойчивость при сбоях
5. Собирать метрики для мониторинга

### Примеры кода

#### Конфигурация Taskiq и FastStream

```python
# src/infrastructure/task_queue/config.py
from pydantic import Field
from pydantic_settings import BaseSettings

class TaskQueueSettings(BaseSettings):
    nats_url: str = Field("nats://localhost:4222", env="NATS_URL")
    nats_stream_name: str = Field("transcription_tasks", env="NATS_STREAM_NAME")
    nats_consumer_name: str = Field("transcription_worker", env="NATS_CONSUMER_NAME")
    task_timeout: int = Field(3600, env="TASK_TIMEOUT")  # 1 hour timeout
    max_retries: int = Field(3, env="TASK_MAX_RETRIES")
    retry_delay: int = Field(30, env="TASK_RETRY_DELAY")  # seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

#### Настройка брокера NATS JetStream

```python
# src/infrastructure/task_queue/broker.py
import asyncio
from faststream.nats import NatsBroker
from faststream.nats.schemas import JetStreamContext
from nats.js.api import StreamConfig, RetentionPolicy, StorageType

from src.infrastructure.task_queue.config import TaskQueueSettings

settings = TaskQueueSettings()

async def setup_nats_jetstream() -> NatsBroker:
    """Setup NATS JetStream broker with proper configuration."""
    broker = NatsBroker(settings.nats_url)
    await broker.connect()
    
    # Get JetStream context
    js: JetStreamContext = broker.get_jetstream_context()
    
    # Create stream if it doesn't exist
    try:
        await js.stream_info(settings.nats_stream_name)
    except Exception:
        # Create stream with proper configuration
        stream_config = StreamConfig(
            name=settings.nats_stream_name,
            subjects=[f"{settings.nats_stream_name}.*"],
            retention=RetentionPolicy.WORK_QUEUE,
            storage=StorageType.FILE,
            max_age=86400 * 7,  # 7 days
            discard="old",
            max_msgs_per_subject=10000,
        )
        await js.add_stream(stream_config)
    
    return broker

# Singleton instance
broker_instance = None

async def get_broker() -> NatsBroker:
    """Get or create broker instance."""
    global broker_instance
    if broker_instance is None:
        broker_instance = await setup_nats_jetstream()
    return broker_instance
```

#### Определение задач с Taskiq

```python
# src/infrastructure/task_queue/tasks.py
import asyncio
import structlog
from typing import Dict, Any, Optional
from uuid import UUID

from taskiq import TaskiqEvents, Context, AsyncBroker
from taskiq.brokers.nats_broker import NatsBroker as TaskiqNatsBroker
from taskiq.serializers import JsonSerializer

from src.infrastructure.task_queue.config import TaskQueueSettings
from src.infrastructure.metrics.prometheus import task_processing_time, task_success_counter, task_failure_counter
from src.domains.transcription.models import TranscriptionTask, TranscriptionResult
from src.domains.diarization.models import DiarizationTask, DiarizationResult

settings = TaskQueueSettings()
logger = structlog.get_logger()

# Create Taskiq broker
broker = TaskiqNatsBroker(
    url=settings.nats_url,
    stream=settings.nats_stream_name,
    serializer=JsonSerializer(),
)

# Register event handlers
@broker.on_event(TaskiqEvents.AFTER_TASK)
async def after_task(context: Context, result: Any, exception: Optional[Exception] = None) -> None:
    """Handle task completion and collect metrics."""
    task_name = context.task_name
    task_id = context.task_id
    execution_time = context.execution_time
    
    # Record task processing time
    task_processing_time.labels(task_name=task_name).observe(execution_time)
    
    if exception is None:
        # Task succeeded
        task_success_counter.labels(task_name=task_name).inc()
        logger.info(
            "Task completed successfully",
            task_id=task_id,
            task_name=task_name,
            execution_time=execution_time,
        )
    else:
        # Task failed
        task_failure_counter.labels(task_name=task_name).inc()
        logger.error(
            "Task failed",
            task_id=task_id,
            task_name=task_name,
            execution_time=execution_time,
            error=str(exception),
        )

# Define tasks
@broker.task(retry_policy={"max_retries": settings.max_retries, "delay": settings.retry_delay})
async def process_transcription(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process transcription task."""
    task_id = task_data.get("task_id")
    logger.info("Starting transcription task", task_id=task_id)
    
    # Convert dict to task model
    task = TranscriptionTask(**task_data)
    
    # Here would be the actual transcription logic
    # This is a placeholder for the actual implementation
    await asyncio.sleep(5)  # Simulate processing
    
    # Update task progress (would be called periodically in real implementation)
    await update_task_progress(task_id, 100)
    
    # Return result
    result = TranscriptionResult(
        task_id=task.task_id,
        audio_file_id=task.audio_file_id,
        text="Transcription result example",
        segments=[],  # Would contain actual segments
        language="ru",
        duration=120.5,
    )
    
    return result.model_dump()

@broker.task(retry_policy={"max_retries": settings.max_retries, "delay": settings.retry_delay})
async def process_diarization(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process diarization task."""
    task_id = task_data.get("task_id")
    logger.info("Starting diarization task", task_id=task_id)
    
    # Convert dict to task model
    task = DiarizationTask(**task_data)
    
    # Here would be the actual diarization logic
    # This is a placeholder for the actual implementation
    await asyncio.sleep(5)  # Simulate processing
    
    # Update task progress (would be called periodically in real implementation)
    await update_task_progress(task_id, 100)
    
    # Return result
    result = DiarizationResult(
        task_id=task.task_id,
        audio_file_id=task.audio_file_id,
        speakers=2,
        segments=[],  # Would contain actual speaker segments
    )
    
    return result.model_dump()

# Task progress tracking
async def update_task_progress(task_id: UUID, progress: int) -> None:
    """Update task progress in Redis."""
    from src.infrastructure.cache.redis import get_redis
    
    redis = await get_redis()
    await redis.set(f"task:{task_id}:progress", str(progress))
    await redis.expire(f"task:{task_id}:progress", 86400)  # 24 hours TTL
    
    logger.debug("Task progress updated", task_id=task_id, progress=progress)
```

#### Сервис для работы с задачами

```python
# src/domains/task/service.py
import uuid
from typing import Dict, Any, Optional
import structlog
from fastapi import Depends

from src.infrastructure.task_queue.tasks import process_transcription, process_diarization, update_task_progress
from src.infrastructure.cache.redis import get_redis
from src.domains.transcription.models import TranscriptionTask
from src.domains.diarization.models import DiarizationTask

logger = structlog.get_logger()

class TaskService:
    """Service for managing tasks."""
    
    def __init__(self, redis=Depends(get_redis)):
        self.redis = redis
    
    async def create_transcription_task(self, audio_file_id: str, user_id: int, 
                                        model: str = "large-v3", language: Optional[str] = None) -> str:
        """Create and enqueue a transcription task."""
        task_id = str(uuid.uuid4())
        
        task = TranscriptionTask(
            task_id=task_id,
            audio_file_id=audio_file_id,
            user_id=user_id,
            model=model,
            language=language,
        )
        
        # Store initial task info in Redis
        await self.redis.set(f"task:{task_id}:info", task.model_dump_json())
        await self.redis.set(f"task:{task_id}:progress", "0")
        await self.redis.expire(f"task:{task_id}:info", 86400 * 7)  # 7 days TTL
        await self.redis.expire(f"task:{task_id}:progress", 86400 * 7)
        
        # Enqueue task
        await process_transcription.kiq(task.model_dump())
        
        logger.info("Transcription task created", task_id=task_id, user_id=user_id)
        return task_id
    
    async def create_diarization_task(self, audio_file_id: str, user_id: int,
                                     min_speakers: Optional[int] = None, 
                                     max_speakers: Optional[int] = None) -> str:
        """Create and enqueue a diarization task."""
        task_id = str(uuid.uuid4())
        
        task = DiarizationTask(
            task_id=task_id,
            audio_file_id=audio_file_id,
            user_id=user_id,
            min_speakers=min_speakers,
            max_speakers=max_speakers,
        )
        
        # Store initial task info in Redis
        await self.redis.set(f"task:{task_id}:info", task.model_dump_json())
        await self.redis.set(f"task:{task_id}:progress", "0")
        await self.redis.expire(f"task:{task_id}:info", 86400 * 7)
        await self.redis.expire(f"task:{task_id}:progress", 86400 * 7)
        
        # Enqueue task
        await process_diarization.kiq(task.model_dump())
        
        logger.info("Diarization task created", task_id=task_id, user_id=user_id)
        return task_id
    
    async def get_task_progress(self, task_id: str) -> int:
        """Get task progress percentage."""
        progress = await self.redis.get(f"task:{task_id}:progress")
        if progress is None:
            return 0
        return int(progress)
    
    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task result if available."""
        result_json = await self.redis.get(f"task:{task_id}:result")
        if result_json is None:
            return None
        
        import json
        return json.loads(result_json)
```

#### Метрики для мониторинга очередей

```python
# src/infrastructure/metrics/prometheus.py
from prometheus_client import Counter, Histogram, Gauge

# Task metrics
task_processing_time = Histogram(
    "task_processing_time_seconds",
    "Time spent processing tasks",
    ["task_name"],
)

task_success_counter = Counter(
    "task_success_total",
    "Number of successfully processed tasks",
    ["task_name"],
)

task_failure_counter = Counter(
    "task_failure_total",
    "Number of failed tasks",
    ["task_name"],
)

task_queue_size = Gauge(
    "task_queue_size",
    "Number of tasks in queue",
    ["queue_name"],
)

task_in_progress = Gauge(
    "task_in_progress",
    "Number of tasks currently being processed",
    ["task_name"],
)

# Periodically update queue size metrics
async def update_queue_metrics():
    """Update queue size metrics from NATS JetStream."""
    from src.infrastructure.task_queue.broker import get_broker
    
    broker = await get_broker()
    js = broker.get_jetstream_context()
    
    # Get stream info
    from src.infrastructure.task_queue.config import TaskQueueSettings
    settings = TaskQueueSettings()
    
    try:
        stream_info = await js.stream_info(settings.nats_stream_name)
        
        # Update metrics
        task_queue_size.labels(queue_name=settings.nats_stream_name).set(
            stream_info.state.messages
        )
    except Exception as e:
        import structlog
        logger = structlog.get_logger()
        logger.error("Failed to update queue metrics", error=str(e))
```

### Конфигурации

#### docker-compose.yml (дополнения)

```yaml
# Добавить в существующий docker-compose.yml
services:
  # ... существующие сервисы ...
  
  nats:
    image: nats:2.9.17-alpine
    command: 
      - "--jetstream"
      - "--store_dir=/data"
      - "--http_port=8222"
    ports:
      - "4222:4222"  # Client connections
      - "8222:8222"  # HTTP monitoring
    volumes:
      - nats-data:/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8222/healthz"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  task-worker:
    build:
      context: .
      dockerfile: Dockerfile
    command: python -m src.worker
    environment:
      - NATS_URL=nats://nats:4222
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:password@postgres:5432/transcription_db
      - LOG_LEVEL=INFO
    depends_on:
      - nats
      - redis
      - postgres
    networks:
      - app-network
    deploy:
      replicas: 2  # Можно масштабировать горизонтально
      resources:
        limits:
          cpus: '1'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G

volumes:
  # ... существующие volumes ...
  nats-data:
```

#### Файл запуска воркера

```python
# src/worker.py
import asyncio
import structlog
from taskiq.cli.run_worker import run_worker

from src.infrastructure.task_queue.tasks import broker
from src.infrastructure.metrics.prometheus import update_queue_metrics
from src.infrastructure.logging.setup import configure_logging

logger = structlog.get_logger()

async def metrics_updater():
    """Periodically update queue metrics."""
    while True:
        try:
            await update_queue_metrics()
        except Exception as e:
            logger.error("Error updating metrics", error=str(e))
        
        await asyncio.sleep(15)  # Update every 15 seconds

async def main():
    """Run worker with metrics updater."""
    configure_logging()
    logger.info("Starting task worker")
    
    # Start metrics updater in background
    asyncio.create_task(metrics_updater())
    
    # Run worker
    await run_worker(broker, "src.infrastructure.task_queue.tasks")

if __name__ == "__main__":
    asyncio.run(main())
```

### Схемы данных/API

#### API для работы с задачами

```python
# src/api/v1/tasks.py
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, UUID4

from src.domains.task.service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])

class TranscriptionTaskCreate(BaseModel):
    """Request model for creating a transcription task."""
    audio_file_id: str
    user_id: int
    model: str = "large-v3"
    language: str = None

class DiarizationTaskCreate(BaseModel):
    """Request model for creating a diarization task."""
    audio_file_id: str
    user_id: int
    min_speakers: int = None
    max_speakers: int = None

class TaskResponse(BaseModel):
    """Response model with task ID."""
    task_id: str

class TaskProgressResponse(BaseModel):
    """Response model with task progress."""
    task_id: str
    progress: int
    result: Dict[str, Any] = None

@router.post("/transcription", response_model=TaskResponse)
async def create_transcription_task(
    task: TranscriptionTaskCreate,
    task_service: TaskService = Depends(),
):
    """Create a new transcription task."""
    task_id = await task_service.create_transcription_task(
        audio_file_id=task.audio_file_id,
        user_id=task.user_id,
        model=task.model,
        language=task.language,
    )
    return TaskResponse(task_id=task_id)

@router.post("/diarization", response_model=TaskResponse)
async def create_diarization_task(
    task: DiarizationTaskCreate,
    task_service: TaskService = Depends(),
):
    """Create a new diarization task."""
    task_id = await task_service.create_diarization_task(
        audio_file_id=task.audio_file_id,
        user_id=task.user_id,
        min_speakers=task.min_speakers,
        max_speakers=task.max_speakers,
    )
    return TaskResponse(task_id=task_id)

@router.get("/{task_id}/progress", response_model=TaskProgressResponse)
async def get_task_progress(
    task_id: str,
    task_service: TaskService = Depends(),
):
    """Get task progress."""
    progress = await task_service.get_task_progress(task_id)
    result = await task_service.get_task_result(task_id)
    
    return TaskProgressResponse(
        task_id=task_id,
        progress=progress,
        result=result,
    )
```

## 2. Практическая секция

### Пошаговые инструкции

1. **Настройка NATS JetStream**
   - Добавьте сервис NATS в docker-compose.yml
   - Создайте конфигурацию для NATS JetStream
   - Настройте хранение данных в volume

2. **Реализация инфраструктуры задач**
   - Создайте модуль `src/infrastructure/task_queue`
   - Реализуйте конфигурацию и брокер для Taskiq
   - Настройте интеграцию с FastStream и NATS

3. **Определение моделей задач**
   - Создайте модели для задач транскрипции и диаризации
   - Добавьте поля для отслеживания прогресса и статуса

4. **Реализация сервиса задач**
   - Создайте сервис для создания и управления задачами
   - Реализуйте методы для получения прогресса и результатов

5. **Настройка метрик и мониторинга**
   - Добавьте Prometheus метрики для задач
   - Реализуйте периодическое обновление метрик очередей

6. **Реализация API для задач**
   - Создайте эндпоинты для создания задач
   - Добавьте эндпоинт для получения прогресса

7. **Реализация воркера**
   - Создайте скрипт для запуска воркера
   - Настройте обработку задач и обновление метрик

8. **Интеграция с существующими сервисами**
   - Обновите сервисы транскрипции и диаризации для работы с задачами
   - Интегрируйте с Redis для хранения прогресса и результатов

### Частые ошибки (Common Pitfalls)

1. **Потеря задач при перезапуске**
   - Убедитесь, что NATS JetStream настроен на сохранение сообщений
   - Используйте правильную политику хранения (retention policy)

2. **Блокировка основного потока**
   - Все операции с задачами должны быть асинхронными
   - Избегайте блокирующих операций в обработчиках задач

3. **Утечки памяти**
   - Закрывайте соединения с NATS и Redis после использования
   - Следите за количеством одновременно обрабатываемых задач

4. **Дублирование задач**
   - Используйте уникальные идентификаторы для задач
   - Проверяйте существование задачи перед созданием новой

5. **Неправильная обработка ошибок**
   - Реализуйте политику повторных попыток для задач
   - Логируйте все ошибки с контекстом для отладки

### Советы по оптимизации (Performance Tips)

1. **Горизонтальное масштабирование**
   - Запускайте несколько экземпляров воркера для параллельной обработки
   - Используйте NATS JetStream для распределения задач

2. **Оптимизация памяти**
   - Устанавливайте ограничения на использование памяти для воркеров
   - Используйте потоковую обработку для больших файлов

3. **Кеширование результатов**
   - Кешируйте промежуточные результаты в Redis
   - Используйте TTL для автоматической очистки устаревших данных

4. **Приоритизация задач**
   - Реализуйте систему приоритетов для задач
   - Обрабатывайте короткие задачи в первую очередь

5. **Мониторинг производительности**
   - Собирайте метрики времени выполнения задач
   - Настройте алерты на длительные задачи

## 3. Валидационная секция

### Чек-лист для самопроверки

- [ ] NATS JetStream настроен и работает в Docker
- [ ] Taskiq и FastStream интегрированы с NATS
- [ ] Реализованы модели для задач транскрипции и диаризации
- [ ] Сервис задач корректно создает и отслеживает задачи
- [ ] API для работы с задачами реализовано и протестировано
- [ ] Метрики для мониторинга очередей настроены
- [ ] Воркер запускается и обрабатывает задачи
- [ ] Прогресс задач корректно отображается
- [ ] Система корректно обрабатывает ошибки и повторные попытки
- [ ] Документация API обновлена с новыми эндпоинтами

### Автоматизированные тесты

```python
# tests/infrastructure/test_task_queue.py
import pytest
import asyncio
from unittest.mock import patch, MagicMock

from src.infrastructure.task_queue.tasks import process_transcription, process_diarization
from src.domains.task.service import TaskService

@pytest.fixture
async def redis_mock():
    """Mock Redis client."""
    redis = MagicMock()
    redis.set = MagicMock(return_value=asyncio.Future())
    redis.set.return_value.set_result(True)
    redis.get = MagicMock(return_value=asyncio.Future())
    redis.get.return_value.set_result(b"50")
    redis.expire = MagicMock(return_value=asyncio.Future())
    redis.expire.return_value.set_result(True)
    return redis

@pytest.mark.asyncio
async def test_create_transcription_task(redis_mock):
    """Test creating a transcription task."""
    with patch("src.infrastructure.task_queue.tasks.process_transcription.kiq") as mock_kiq:
        mock_kiq.return_value = asyncio.Future()
        mock_kiq.return_value.set_result(None)
        
        service = TaskService(redis=redis_mock)
        task_id = await service.create_transcription_task(
            audio_file_id="test_audio.mp3",
            user_id=123,
            model="large-v3",
        )
        
        # Check that task was created
        assert task_id is not None
        assert len(task_id) > 0
        
        # Check that task was enqueued
        mock_kiq.assert_called_once()
        
        # Check that Redis was updated
        redis_mock.set.assert_called()
        redis_mock.expire.assert_called()

@pytest.mark.asyncio
async def test_get_task_progress(redis_mock):
    """Test getting task progress."""
    service = TaskService(redis=redis_mock)
    progress = await service.get_task_progress("test-task-id")
    
    # Check that progress was retrieved
    assert progress == 50
    
    # Check that Redis was queried
    redis_mock.get.assert_called_with("task:test-task-id:progress")

@pytest.mark.asyncio
async def test_process_transcription():
    """Test processing a transcription task."""
    with patch("src.infrastructure.task_queue.tasks.update_task_progress") as mock_update:
        mock_update.return_value = asyncio.Future()
        mock_update.return_value.set_result(None)
        
        task_data = {
            "task_id": "test-task-id",
            "audio_file_id": "test_audio.mp3",
            "user_id": 123,
            "model": "large-v3",
        }
        
        result = await process_transcription(task_data)
        
        # Check that result was returned
        assert result is not None
        assert "task_id" in result
        assert result["task_id"] == "test-task-id"
        
        # Check that progress was updated
        mock_update.assert_called_with("test-task-id", 100)
```

### Критерии для ручного тестирования

1. **Создание задачи транскрипции**
   - Отправьте POST запрос на `/api/v1/tasks/transcription`
   - Проверьте, что возвращается task_id
   - Проверьте, что задача появляется в очереди NATS

2. **Отслеживание прогресса**
   - Создайте задачу и получите task_id
   - Отправьте GET запрос на `/api/v1/tasks/{task_id}/progress`
   - Проверьте, что прогресс обновляется со временем

3. **Обработка ошибок**
   - Создайте задачу с некорректными данными
   - Проверьте, что система корректно обрабатывает ошибку
   - Проверьте, что задача помечается как неудачная после исчерпания повторных попыток

4. **Масштабирование**
   - Запустите несколько экземпляров воркера
   - Создайте несколько задач одновременно
   - Проверьте, что задачи распределяются между воркерами

5. **Мониторинг**
   - Проверьте, что метрики доступны в Prometheus
   - Проверьте, что графики в Grafana отображают активность очередей
   - Проверьте, что логи содержат информацию о выполнении задач