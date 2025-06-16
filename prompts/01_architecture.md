# Фаза 1, День 1. Архитектура и проектирование системы

## Цель (Definition of Done)
- Спроектирована архитектура системы в соответствии с принципами DDD
- Определены основные домены, их границы и взаимодействия
- Созданы интерфейсы для ключевых компонентов системы
- Разработана структура проекта с учетом микросервисной архитектуры
- Подготовлена документация по архитектуре системы

## Ссылки на документацию
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Python Application Layouts](https://realpython.com/python-application-layouts/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [aiogram 3.x Documentation](https://docs.aiogram.dev/en/latest/)
- [Event-Driven Architecture](https://microservices.io/patterns/data/event-driven-architecture.html)

---

### 1. Техническая секция

#### Описание
В этом задании необходимо спроектировать архитектуру Telegram-бота для транскрипции аудио с диаризацией спикеров. Система должна следовать принципам Domain-Driven Design (DDD) и быть построена на микросервисной архитектуре.

Основные домены системы:
1. **Audio Domain** - обработка и валидация аудиофайлов
2. **Transcription Domain** - транскрипция аудио с использованием Whisper
3. **Diarization Domain** - разделение аудио по спикерам
4. **Export Domain** - экспорт результатов в различные форматы
5. **User Domain** - управление пользователями и их настройками

Система должна использовать Event-Driven Architecture для асинхронной обработки длительных задач и обеспечения масштабируемости.

#### Примеры кода

**Структура проекта:**
```
src/
├── domains/
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── entities.py
│   │   ├── repositories.py
│   │   ├── services.py
│   │   └── exceptions.py
│   ├── transcription/
│   │   ├── __init__.py
│   │   ├── entities.py
│   │   ├── repositories.py
│   │   ├── services.py
│   │   └── exceptions.py
│   ├── diarization/
│   │   ├── __init__.py
│   │   ├── entities.py
│   │   ├── repositories.py
│   │   ├── services.py
│   │   └── exceptions.py
│   ├── export/
│   │   ├── __init__.py
│   │   ├── entities.py
│   │   ├── repositories.py
│   │   ├── services.py
│   │   └── exceptions.py
│   └── user/
│       ├── __init__.py
│       ├── entities.py
│       ├── repositories.py
│       ├── services.py
│       └── exceptions.py
├── infrastructure/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── repositories.py
│   ├── messaging/
│   │   ├── __init__.py
│   │   ├── nats_client.py
│   │   └── event_bus.py
│   ├── storage/
│   │   ├── __init__.py
│   │   └── object_storage.py
│   └── telegram/
│       ├── __init__.py
│       ├── bot.py
│       └── dialogs/
├── application/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   └── dependencies.py
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── handlers/
│   │   └── middlewares/
│   └── services/
│       ├── __init__.py
│       ├── audio_service.py
│       ├── transcription_service.py
│       ├── diarization_service.py
│       └── export_service.py
├── config/
│   ├── __init__.py
│   └── settings.py
└── main.py
```

**Пример интерфейса для Audio Domain:**
```python
# src/domains/audio/entities.py
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class AudioFormat(str, Enum):
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    M4A = "m4a"
    WEBM = "webm"


@dataclass
class AudioFile:
    id: str
    user_id: int
    original_filename: str
    format: AudioFormat
    size_bytes: int
    duration_seconds: Optional[float] = None
    path: Optional[Path] = None
    processed_path: Optional[Path] = None
    is_valid: bool = False
    error_message: Optional[str] = None


# src/domains/audio/repositories.py
from abc import ABC, abstractmethod
from typing import Optional

from .entities import AudioFile


class AudioRepository(ABC):
    @abstractmethod
    async def save(self, audio_file: AudioFile) -> AudioFile:
        pass

    @abstractmethod
    async def get_by_id(self, file_id: str) -> Optional[AudioFile]:
        pass

    @abstractmethod
    async def update(self, audio_file: AudioFile) -> AudioFile:
        pass

    @abstractmethod
    async def delete(self, file_id: str) -> None:
        pass


# src/domains/audio/services.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional

from .entities import AudioFile, AudioFormat


class AudioService(ABC):
    @abstractmethod
    async def validate_audio(self, file: BinaryIO, filename: str, user_id: int) -> AudioFile:
        """Validate audio file and create AudioFile entity"""
        pass

    @abstractmethod
    async def convert_to_wav(self, audio_file: AudioFile) -> Path:
        """Convert audio to WAV format for processing"""
        pass

    @abstractmethod
    async def get_audio_duration(self, file_path: Path) -> float:
        """Get audio duration in seconds"""
        pass

    @abstractmethod
    async def normalize_volume(self, file_path: Path) -> Path:
        """Normalize audio volume"""
        pass

    @abstractmethod
    async def detect_silence(self, file_path: Path) -> list[tuple[float, float]]:
        """Detect silence periods in audio file"""
        pass
```

**Пример интерфейса для Transcription Domain:**
```python
# src/domains/transcription/entities.py
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class TranscriptionModel(str, Enum):
    WHISPER_LARGE_V3 = "whisper-large-v3"
    WHISPER_TURBO = "whisper-turbo"


class TranscriptionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TranscriptionSegment:
    start_time: float  # in seconds
    end_time: float  # in seconds
    text: str
    confidence: float


@dataclass
class Transcription:
    id: str
    audio_file_id: str
    user_id: int
    model: TranscriptionModel
    status: TranscriptionStatus
    language: Optional[str] = None
    segments: List[TranscriptionSegment] = None
    error_message: Optional[str] = None


# src/domains/transcription/services.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from .entities import Transcription, TranscriptionModel, TranscriptionSegment


class TranscriptionService(ABC):
    @abstractmethod
    async def create_transcription_task(
        self, audio_file_id: str, user_id: int, model: TranscriptionModel
    ) -> Transcription:
        """Create a new transcription task"""
        pass

    @abstractmethod
    async def transcribe(self, transcription_id: str) -> Transcription:
        """Process transcription task"""
        pass

    @abstractmethod
    async def get_transcription(self, transcription_id: str) -> Optional[Transcription]:
        """Get transcription by ID"""
        pass

    @abstractmethod
    async def detect_language(self, audio_path: Path) -> str:
        """Detect language of the audio file"""
        pass
```

#### Схемы данных/API

**Database Schema:**
```sql
-- Audio files table
CREATE TABLE audio_files (
    id UUID PRIMARY KEY,
    user_id BIGINT NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    format VARCHAR(10) NOT NULL,
    size_bytes BIGINT NOT NULL,
    duration_seconds FLOAT,
    path VARCHAR(255),
    processed_path VARCHAR(255),
    is_valid BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Transcriptions table
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY,
    audio_file_id UUID NOT NULL REFERENCES audio_files(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    model VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    language VARCHAR(10),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Transcription segments table
CREATE TABLE transcription_segments (
    id UUID PRIMARY KEY,
    transcription_id UUID NOT NULL REFERENCES transcriptions(id) ON DELETE CASCADE,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    text TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Diarization table
CREATE TABLE diarizations (
    id UUID PRIMARY KEY,
    audio_file_id UUID NOT NULL REFERENCES audio_files(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL,
    num_speakers INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Speaker segments table
CREATE TABLE speaker_segments (
    id UUID PRIMARY KEY,
    diarization_id UUID NOT NULL REFERENCES diarizations(id) ON DELETE CASCADE,
    speaker_id INTEGER NOT NULL,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    language_code VARCHAR(10),
    is_premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User settings table
CREATE TABLE user_settings (
    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    preferred_model VARCHAR(50) NOT NULL DEFAULT 'whisper-large-v3',
    preferred_export_format VARCHAR(20) NOT NULL DEFAULT 'docx',
    auto_detect_language BOOLEAN DEFAULT TRUE,
    auto_delete_files BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**API Specification:**
```yaml
openapi: 3.0.0
info:
  title: Audio Transcription API
  version: 1.0.0
  description: API for audio transcription with speaker diarization

paths:
  /api/audio:
    post:
      summary: Upload audio file
      operationId: uploadAudio
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
      responses:
        '200':
          description: Audio file uploaded successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AudioFile'
        '400':
          description: Invalid audio file
        '413':
          description: File too large

  /api/audio/{audio_id}:
    get:
      summary: Get audio file info
      operationId: getAudio
      parameters:
        - name: audio_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Audio file info
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AudioFile'
        '404':
          description: Audio file not found

  /api/transcription:
    post:
      summary: Create transcription task
      operationId: createTranscription
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                audio_id:
                  type: string
                  format: uuid
                model:
                  type: string
                  enum: [whisper-large-v3, whisper-turbo]
      responses:
        '200':
          description: Transcription task created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Transcription'
        '400':
          description: Invalid request
        '404':
          description: Audio file not found

  /api/transcription/{transcription_id}:
    get:
      summary: Get transcription
      operationId: getTranscription
      parameters:
        - name: transcription_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Transcription info
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Transcription'
        '404':
          description: Transcription not found

components:
  schemas:
    AudioFile:
      type: object
      properties:
        id:
          type: string
          format: uuid
        user_id:
          type: integer
          format: int64
        original_filename:
          type: string
        format:
          type: string
          enum: [mp3, wav, ogg, m4a, webm]
        size_bytes:
          type: integer
          format: int64
        duration_seconds:
          type: number
          format: float
        is_valid:
          type: boolean
        error_message:
          type: string
        created_at:
          type: string
          format: date-time

    Transcription:
      type: object
      properties:
        id:
          type: string
          format: uuid
        audio_file_id:
          type: string
          format: uuid
        user_id:
          type: integer
          format: int64
        model:
          type: string
          enum: [whisper-large-v3, whisper-turbo]
        status:
          type: string
          enum: [pending, in_progress, completed, failed]
        language:
          type: string
        segments:
          type: array
          items:
            $ref: '#/components/schemas/TranscriptionSegment'
        error_message:
          type: string
        created_at:
          type: string
          format: date-time

    TranscriptionSegment:
      type: object
      properties:
        start_time:
          type: number
          format: float
        end_time:
          type: number
          format: float
        text:
          type: string
        confidence:
          type: number
          format: float
```

### 2. Практическая секция

#### Пошаговые инструкции

1. **Создание базовой структуры проекта**:
   - Создайте структуру каталогов согласно приведенной выше схеме
   - Инициализируйте Git-репозиторий и добавьте .gitignore
   - Настройте pyproject.toml с необходимыми зависимостями

2. **Определение доменных моделей**:
   - Для каждого домена создайте файлы entities.py с основными сущностями
   - Определите перечисления (Enum) для статусов и типов
   - Используйте dataclasses для определения сущностей

3. **Создание интерфейсов репозиториев**:
   - Для каждого домена создайте абстрактные классы репозиториев
   - Определите методы CRUD для каждой сущности
   - Используйте typing для аннотации типов

4. **Определение сервисных интерфейсов**:
   - Создайте абстрактные классы сервисов для каждого домена
   - Определите методы бизнес-логики
   - Используйте typing для аннотации типов

5. **Настройка инфраструктурного слоя**:
   - Создайте базовые классы для работы с базой данных
   - Настройте клиент для работы с NATS
   - Создайте классы для работы с объектным хранилищем

6. **Документирование архитектуры**:
   - Создайте README.md с описанием архитектуры
   - Добавьте диаграммы взаимодействия компонентов
   - Опишите потоки данных между сервисами

#### Частые ошибки (Common Pitfalls)

1. **Нарушение принципов DDD**:
   - Смешивание бизнес-логики с инфраструктурным кодом
   - Нарушение границ доменов
   - Использование анемичных моделей

2. **Проблемы с абстракциями**:
   - Слишком абстрактные интерфейсы, которые сложно реализовать
   - Слишком конкретные интерфейсы, которые сложно расширить
   - Отсутствие четких контрактов между компонентами

3. **Проблемы с масштабируемостью**:
   - Недостаточное разделение на микросервисы
   - Тесная связь между компонентами
   - Отсутствие асинхронной обработки длительных задач

#### Советы по оптимизации (Performance Tips)

1. **Оптимизация структуры проекта**:
   - Используйте lazy loading для импортов
   - Разделяйте код на модули по функциональности
   - Избегайте циклических зависимостей

2. **Оптимизация работы с базой данных**:
   - Используйте индексы для часто запрашиваемых полей
   - Применяйте пагинацию для больших наборов данных
   - Используйте транзакции для атомарных операций

3. **Оптимизация асинхронной обработки**:
   - Используйте пулы для ограничения параллельных задач
   - Применяйте backpressure для контроля нагрузки
   - Реализуйте механизмы повторных попыток для обработки ошибок

### 3. Валидационная секция

#### Чек-лист для самопроверки

- [ ] Структура проекта соответствует принципам DDD
- [ ] Определены все необходимые домены и их границы
- [ ] Созданы интерфейсы для всех ключевых компонентов
- [ ] Определены сущности для всех доменов
- [ ] Созданы абстрактные классы репозиториев
- [ ] Определены сервисные интерфейсы
- [ ] Настроена базовая инфраструктура
- [ ] Документирована архитектура системы
- [ ] Код соответствует PEP 8 и включает типизацию
- [ ] Структура базы данных соответствует доменной модели

#### Автоматизированные тесты

```python
# tests/domains/audio/test_entities.py
import pytest
from pathlib import Path

from src.domains.audio.entities import AudioFile, AudioFormat


def test_audio_file_creation():
    audio_file = AudioFile(
        id="123e4567-e89b-12d3-a456-426614174000",
        user_id=123456789,
        original_filename="test_audio.mp3",
        format=AudioFormat.MP3,
        size_bytes=1024000,
        duration_seconds=60.5,
        path=Path("/tmp/audio/123e4567-e89b-12d3-a456-426614174000.mp3"),
        is_valid=True
    )
    
    assert audio_file.id == "123e4567-e89b-12d3-a456-426614174000"
    assert audio_file.user_id == 123456789
    assert audio_file.original_filename == "test_audio.mp3"
    assert audio_file.format == AudioFormat.MP3
    assert audio_file.size_bytes == 1024000
    assert audio_file.duration_seconds == 60.5
    assert audio_file.path == Path("/tmp/audio/123e4567-e89b-12d3-a456-426614174000.mp3")
    assert audio_file.is_valid is True
    assert audio_file.error_message is None


def test_audio_format_enum():
    assert AudioFormat.MP3 == "mp3"
    assert AudioFormat.WAV == "wav"
    assert AudioFormat.OGG == "ogg"
    assert AudioFormat.M4A == "m4a"
    assert AudioFormat.WEBM == "webm"
```

#### Критерии для ручного тестирования

1. **Проверка структуры проекта**:
   - Все необходимые каталоги и файлы созданы
   - Структура соответствует принципам DDD
   - Файлы __init__.py присутствуют во всех пакетах

2. **Проверка доменных моделей**:
   - Все сущности определены и имеют необходимые поля
   - Используются правильные типы данных
   - Перечисления определены корректно

3. **Проверка интерфейсов**:
   - Все абстрактные методы определены
   - Типы аргументов и возвращаемых значений указаны
   - Документация методов присутствует

4. **Проверка документации**:
   - README.md содержит описание архитектуры
   - Диаграммы взаимодействия компонентов присутствуют
   - Потоки данных между сервисами описаны

## Вопросы к постановщику задачи
1. Какие дополнительные метаданные нужно хранить для аудиофайлов?
2. Требуется ли поддержка многоязычной транскрипции в рамках одного файла?
3. Какие конкретные метрики производительности нужно отслеживать для каждого сервиса?
4. Какие ограничения по ресурсам (CPU, RAM) существуют для развертывания системы?
5. Требуется ли интеграция с внешними системами помимо Telegram?

## Ответы на 16.06.25
1. Не знаю.
2. Скорее всего нет. Планируется использование только русскоязычной аудитории.
3. Не знаю.
4. Пока не известно.
5. На текущий момент нет.