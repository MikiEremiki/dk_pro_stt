# Фаза 1, День 5. API спецификация

## Цель (Definition of Done)
- Разработана спецификация API в формате OpenAPI 3.0
- Определены все необходимые эндпоинты для работы с аудиофайлами, транскрипцией и диаризацией
- Настроена базовая структура FastAPI приложения
- Реализованы базовые эндпоинты для проверки работоспособности API
- Настроена автоматическая генерация документации API
- Реализованы схемы данных с использованием Pydantic

## Ссылки на документацию
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)

---

### 1. Техническая секция

#### Описание
В этом задании необходимо разработать спецификацию API для сервиса транскрипции аудио с диаризацией спикеров. API должно предоставлять возможность загрузки аудиофайлов, запуска процессов транскрипции и диаризации, а также получения результатов в различных форматах.

Основные компоненты API:
1. **Аутентификация и авторизация** - защита API от несанкционированного доступа
2. **Управление аудиофайлами** - загрузка, получение информации, удаление
3. **Управление транскрипцией** - создание задач, получение статуса и результатов
4. **Управление диаризацией** - создание задач, получение статуса и результатов
5. **Экспорт результатов** - получение результатов в различных форматах (DOCX, SRT, JSON, TXT)
6. **Мониторинг и метрики** - получение информации о состоянии системы

#### Примеры кода

**OpenAPI спецификация:**
```yaml
# openapi.yaml
openapi: 3.0.3
info:
  title: Audio Transcription API
  description: API for audio transcription with speaker diarization
  version: 1.0.0
  contact:
    name: Support Team
    email: support@example.com

servers:
  - url: https://api.example.com/v1
    description: Production server
  - url: https://staging-api.example.com/v1
    description: Staging server
  - url: http://localhost:8000/v1
    description: Local development server

tags:
  - name: auth
    description: Authentication operations
  - name: audio
    description: Audio file operations
  - name: transcription
    description: Transcription operations
  - name: diarization
    description: Speaker diarization operations
  - name: export
    description: Export operations
  - name: health
    description: Health check operations

paths:
  /auth/token:
    post:
      tags:
        - auth
      summary: Get access token
      description: Get JWT access token for API access
      operationId: getToken
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TokenRequest'
      responses:
        '200':
          description: Successful operation
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenResponse'
        '401':
          description: Invalid credentials
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /audio:
    post:
      tags:
        - audio
      summary: Upload audio file
      description: Upload a new audio file for processing
      operationId: uploadAudio
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
                  description: Audio file to upload
      responses:
        '201':
          description: Audio file uploaded successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AudioFile'
        '400':
          description: Invalid file format or size
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
    
    get:
      tags:
        - audio
      summary: List audio files
      description: Get a list of audio files uploaded by the user
      operationId: listAudioFiles
      security:
        - bearerAuth: []
      parameters:
        - name: page
          in: query
          description: Page number
          required: false
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          description: Number of items per page
          required: false
          schema:
            type: integer
            default: 10
      responses:
        '200':
          description: List of audio files
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items:
                      $ref: '#/components/schemas/AudioFile'
                  total:
                    type: integer
                  page:
                    type: integer
                  limit:
                    type: integer
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /audio/{audio_id}:
    get:
      tags:
        - audio
      summary: Get audio file
      description: Get information about a specific audio file
      operationId: getAudioFile
      security:
        - bearerAuth: []
      parameters:
        - name: audio_id
          in: path
          description: ID of the audio file
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Audio file information
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AudioFile'
        '404':
          description: Audio file not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
    
    delete:
      tags:
        - audio
      summary: Delete audio file
      description: Delete a specific audio file
      operationId: deleteAudioFile
      security:
        - bearerAuth: []
      parameters:
        - name: audio_id
          in: path
          description: ID of the audio file
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '204':
          description: Audio file deleted successfully
        '404':
          description: Audio file not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /transcription:
    post:
      tags:
        - transcription
      summary: Create transcription
      description: Create a new transcription task for an audio file
      operationId: createTranscription
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TranscriptionRequest'
      responses:
        '201':
          description: Transcription task created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Transcription'
        '400':
          description: Invalid request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Audio file not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
    
    get:
      tags:
        - transcription
      summary: List transcriptions
      description: Get a list of transcription tasks created by the user
      operationId: listTranscriptions
      security:
        - bearerAuth: []
      parameters:
        - name: page
          in: query
          description: Page number
          required: false
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          description: Number of items per page
          required: false
          schema:
            type: integer
            default: 10
        - name: status
          in: query
          description: Filter by status
          required: false
          schema:
            type: string
            enum: [pending, in_progress, completed, failed]
      responses:
        '200':
          description: List of transcription tasks
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items:
                      $ref: '#/components/schemas/Transcription'
                  total:
                    type: integer
                  page:
                    type: integer
                  limit:
                    type: integer
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /transcription/{transcription_id}:
    get:
      tags:
        - transcription
      summary: Get transcription
      description: Get information about a specific transcription task
      operationId: getTranscription
      security:
        - bearerAuth: []
      parameters:
        - name: transcription_id
          in: path
          description: ID of the transcription task
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Transcription task information
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Transcription'
        '404':
          description: Transcription task not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /diarization:
    post:
      tags:
        - diarization
      summary: Create diarization
      description: Create a new diarization task for an audio file
      operationId: createDiarization
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DiarizationRequest'
      responses:
        '201':
          description: Diarization task created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Diarization'
        '400':
          description: Invalid request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Audio file not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /diarization/{diarization_id}:
    get:
      tags:
        - diarization
      summary: Get diarization
      description: Get information about a specific diarization task
      operationId: getDiarization
      security:
        - bearerAuth: []
      parameters:
        - name: diarization_id
          in: path
          description: ID of the diarization task
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Diarization task information
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Diarization'
        '404':
          description: Diarization task not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /export/{transcription_id}:
    get:
      tags:
        - export
      summary: Export transcription
      description: Export transcription results in various formats
      operationId: exportTranscription
      security:
        - bearerAuth: []
      parameters:
        - name: transcription_id
          in: path
          description: ID of the transcription task
          required: true
          schema:
            type: string
            format: uuid
        - name: format
          in: query
          description: Export format
          required: true
          schema:
            type: string
            enum: [docx, srt, json, txt]
        - name: include_diarization
          in: query
          description: Include diarization information if available
          required: false
          schema:
            type: boolean
            default: true
      responses:
        '200':
          description: Exported file
          content:
            application/vnd.openxmlformats-officedocument.wordprocessingml.document:
              schema:
                type: string
                format: binary
            application/x-subrip:
              schema:
                type: string
                format: binary
            application/json:
              schema:
                type: object
            text/plain:
              schema:
                type: string
        '404':
          description: Transcription task not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /health:
    get:
      tags:
        - health
      summary: Health check
      description: Check the health of the API
      operationId: healthCheck
      responses:
        '200':
          description: API is healthy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Health'

  /health/detailed:
    get:
      tags:
        - health
      summary: Detailed health check
      description: Check the health of all API components
      operationId: detailedHealthCheck
      security:
        - bearerAuth: []
      responses:
        '200':
          description: Detailed health information
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DetailedHealth'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

components:
  schemas:
    TokenRequest:
      type: object
      required:
        - username
        - password
      properties:
        username:
          type: string
          description: Username or email
        password:
          type: string
          format: password
          description: User password

    TokenResponse:
      type: object
      properties:
        access_token:
          type: string
          description: JWT access token
        token_type:
          type: string
          default: bearer
        expires_in:
          type: integer
          description: Token expiration time in seconds

    AudioFile:
      type: object
      properties:
        id:
          type: string
          format: uuid
          description: Unique identifier for the audio file
        user_id:
          type: integer
          format: int64
          description: ID of the user who uploaded the file
        original_filename:
          type: string
          description: Original filename
        format:
          type: string
          enum: [mp3, wav, ogg, m4a, webm]
          description: Audio format
        size_bytes:
          type: integer
          format: int64
          description: File size in bytes
        duration_seconds:
          type: number
          format: float
          description: Audio duration in seconds
        is_valid:
          type: boolean
          description: Whether the file is valid and can be processed
        created_at:
          type: string
          format: date-time
          description: Creation timestamp
        updated_at:
          type: string
          format: date-time
          description: Last update timestamp

    TranscriptionRequest:
      type: object
      required:
        - audio_id
      properties:
        audio_id:
          type: string
          format: uuid
          description: ID of the audio file to transcribe
        model:
          type: string
          enum: [whisper-large-v3, whisper-turbo]
          default: whisper-large-v3
          description: Transcription model to use
        language:
          type: string
          description: Language code (leave empty for auto-detection)
        auto_detect_language:
          type: boolean
          default: true
          description: Whether to auto-detect the language

    Transcription:
      type: object
      properties:
        id:
          type: string
          format: uuid
          description: Unique identifier for the transcription task
        audio_id:
          type: string
          format: uuid
          description: ID of the audio file
        user_id:
          type: integer
          format: int64
          description: ID of the user who created the task
        model:
          type: string
          enum: [whisper-large-v3, whisper-turbo]
          description: Transcription model used
        status:
          type: string
          enum: [pending, in_progress, completed, failed]
          description: Current status of the task
        language:
          type: string
          description: Detected or specified language
        progress:
          type: integer
          minimum: 0
          maximum: 100
          description: Progress percentage
        error_message:
          type: string
          description: Error message if the task failed
        segments:
          type: array
          items:
            $ref: '#/components/schemas/TranscriptionSegment'
          description: Transcription segments
        created_at:
          type: string
          format: date-time
          description: Creation timestamp
        updated_at:
          type: string
          format: date-time
          description: Last update timestamp

    TranscriptionSegment:
      type: object
      properties:
        id:
          type: string
          format: uuid
          description: Unique identifier for the segment
        start_time:
          type: number
          format: float
          description: Start time in seconds
        end_time:
          type: number
          format: float
          description: End time in seconds
        text:
          type: string
          description: Transcribed text
        confidence:
          type: number
          format: float
          minimum: 0
          maximum: 1
          description: Confidence score

    DiarizationRequest:
      type: object
      required:
        - audio_id
      properties:
        audio_id:
          type: string
          format: uuid
          description: ID of the audio file to diarize
        num_speakers:
          type: integer
          minimum: 0
          description: Number of speakers (0 for auto-detection)
        min_speakers:
          type: integer
          minimum: 1
          default: 1
          description: Minimum number of speakers
        max_speakers:
          type: integer
          minimum: 1
          default: 10
          description: Maximum number of speakers

    Diarization:
      type: object
      properties:
        id:
          type: string
          format: uuid
          description: Unique identifier for the diarization task
        audio_id:
          type: string
          format: uuid
          description: ID of the audio file
        user_id:
          type: integer
          format: int64
          description: ID of the user who created the task
        status:
          type: string
          enum: [pending, in_progress, completed, failed]
          description: Current status of the task
        num_speakers:
          type: integer
          description: Number of speakers detected
        progress:
          type: integer
          minimum: 0
          maximum: 100
          description: Progress percentage
        error_message:
          type: string
          description: Error message if the task failed
        segments:
          type: array
          items:
            $ref: '#/components/schemas/DiarizationSegment'
          description: Diarization segments
        created_at:
          type: string
          format: date-time
          description: Creation timestamp
        updated_at:
          type: string
          format: date-time
          description: Last update timestamp

    DiarizationSegment:
      type: object
      properties:
        id:
          type: string
          format: uuid
          description: Unique identifier for the segment
        speaker_id:
          type: integer
          description: Speaker identifier
        start_time:
          type: number
          format: float
          description: Start time in seconds
        end_time:
          type: number
          format: float
          description: End time in seconds
        confidence:
          type: number
          format: float
          minimum: 0
          maximum: 1
          description: Confidence score

    Health:
      type: object
      properties:
        status:
          type: string
          enum: [ok, degraded, down]
          description: Overall health status
        version:
          type: string
          description: API version

    DetailedHealth:
      type: object
      properties:
        status:
          type: string
          enum: [ok, degraded, down]
          description: Overall health status
        version:
          type: string
          description: API version
        components:
          type: object
          additionalProperties:
            type: object
            properties:
              status:
                type: string
                enum: [ok, degraded, down]
              details:
                type: object
                additionalProperties: true

    Error:
      type: object
      properties:
        code:
          type: string
          description: Error code
        message:
          type: string
          description: Error message
        details:
          type: object
          additionalProperties: true
          description: Additional error details

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

**Pydantic модели:**
```python
# src/domains/audio/schemas.py
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AudioFormat(str, Enum):
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    M4A = "m4a"
    WEBM = "webm"


class AudioFileBase(BaseModel):
    """Base schema for audio file."""
    original_filename: str
    format: AudioFormat
    size_bytes: int
    duration_seconds: Optional[float] = None
    is_valid: bool = False


class AudioFileCreate(AudioFileBase):
    """Schema for creating a new audio file."""
    pass


class AudioFileUpdate(BaseModel):
    """Schema for updating an audio file."""
    duration_seconds: Optional[float] = None
    is_valid: Optional[bool] = None


class AudioFileInDB(AudioFileBase):
    """Schema for audio file in database."""
    id: UUID
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AudioFileResponse(AudioFileInDB):
    """Schema for audio file response."""
    pass


# src/domains/transcription/schemas.py
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TranscriptionModel(str, Enum):
    WHISPER_LARGE_V3 = "whisper-large-v3"
    WHISPER_TURBO = "whisper-turbo"


class TranscriptionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscriptionSegmentBase(BaseModel):
    """Base schema for transcription segment."""
    start_time: float
    end_time: float
    text: str
    confidence: float


class TranscriptionSegmentCreate(TranscriptionSegmentBase):
    """Schema for creating a new transcription segment."""
    transcription_id: UUID


class TranscriptionSegmentInDB(TranscriptionSegmentBase):
    """Schema for transcription segment in database."""
    id: UUID
    transcription_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class TranscriptionSegmentResponse(TranscriptionSegmentBase):
    """Schema for transcription segment response."""
    id: UUID


class TranscriptionBase(BaseModel):
    """Base schema for transcription."""
    audio_id: UUID
    model: TranscriptionModel
    language: Optional[str] = None
    status: TranscriptionStatus = TranscriptionStatus.PENDING
    progress: int = 0
    error_message: Optional[str] = None


class TranscriptionCreate(BaseModel):
    """Schema for creating a new transcription."""
    audio_id: UUID
    model: TranscriptionModel = TranscriptionModel.WHISPER_LARGE_V3
    language: Optional[str] = None
    auto_detect_language: bool = True


class TranscriptionUpdate(BaseModel):
    """Schema for updating a transcription."""
    language: Optional[str] = None
    status: Optional[TranscriptionStatus] = None
    progress: Optional[int] = None
    error_message: Optional[str] = None


class TranscriptionInDB(TranscriptionBase):
    """Schema for transcription in database."""
    id: UUID
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TranscriptionResponse(TranscriptionInDB):
    """Schema for transcription response."""
    segments: Optional[List[TranscriptionSegmentResponse]] = None


# src/domains/diarization/schemas.py
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DiarizationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class DiarizationSegmentBase(BaseModel):
    """Base schema for diarization segment."""
    speaker_id: int
    start_time: float
    end_time: float
    confidence: float


class DiarizationSegmentCreate(DiarizationSegmentBase):
    """Schema for creating a new diarization segment."""
    diarization_id: UUID


class DiarizationSegmentInDB(DiarizationSegmentBase):
    """Schema for diarization segment in database."""
    id: UUID
    diarization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class DiarizationSegmentResponse(DiarizationSegmentBase):
    """Schema for diarization segment response."""
    id: UUID


class DiarizationBase(BaseModel):
    """Base schema for diarization."""
    audio_id: UUID
    status: DiarizationStatus = DiarizationStatus.PENDING
    num_speakers: Optional[int] = None
    progress: int = 0
    error_message: Optional[str] = None


class DiarizationCreate(BaseModel):
    """Schema for creating a new diarization."""
    audio_id: UUID
    num_speakers: int = 0
    min_speakers: int = 1
    max_speakers: int = 10


class DiarizationUpdate(BaseModel):
    """Schema for updating a diarization."""
    status: Optional[DiarizationStatus] = None
    num_speakers: Optional[int] = None
    progress: Optional[int] = None
    error_message: Optional[str] = None


class DiarizationInDB(DiarizationBase):
    """Schema for diarization in database."""
    id: UUID
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DiarizationResponse(DiarizationInDB):
    """Schema for diarization response."""
    segments: Optional[List[DiarizationSegmentResponse]] = None
```

**FastAPI приложение:**
```python
# src/application/api/main.py
import time
from typing import Dict, List, Optional

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from src.application.api.routes import audio, diarization, export, health, transcription
from src.config.settings import config
from src.domains.user.schemas import TokenResponse, UserResponse

# Настройка логирования
logger = structlog.get_logger()

# Создание приложения
app = FastAPI(
    title="Audio Transcription API",
    description="API for audio transcription with speaker diarization",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Логирование запроса
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client=request.client.host if request.client else None,
    )
    
    # Выполнение запроса
    response = await call_next(request)
    
    # Логирование ответа
    process_time = time.time() - start_time
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=f"{process_time:.4f}s",
    )
    
    return response

# Обработчик ошибок
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "details": exc.headers,
        },
    )

# Документация
@app.get("/docs", include_in_schema=False)
async def get_swagger_documentation():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )

@app.get("/redoc", include_in_schema=False)
async def get_redoc_documentation():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="API Documentation",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )

@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_schema():
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

# Аутентификация
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

@app.post("/auth/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # В реальном приложении здесь будет проверка учетных данных
    # и генерация JWT токена
    if form_data.username != "test" or form_data.password != "test":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "access_token": "dummy_token",
        "token_type": "bearer",
        "expires_in": 3600,
    }

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # В реальном приложении здесь будет проверка токена
    # и получение информации о пользователе
    return {
        "id": 1,
        "username": "test",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
    }

# Подключение роутеров
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(audio.router, prefix="/audio", tags=["audio"])
app.include_router(transcription.router, prefix="/transcription", tags=["transcription"])
app.include_router(diarization.router, prefix="/diarization", tags=["diarization"])
app.include_router(export.router, prefix="/export", tags=["export"])

# Корневой эндпоинт
@app.get("/")
async def root():
    return {
        "name": "Audio Transcription API",
        "version": app.version,
        "docs": "/docs",
        "redoc": "/redoc",
    }
```

**Роутер для аудиофайлов:**
```python
# src/application/api/routes/audio.py
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.api.dependencies import get_current_user, get_db
from src.domains.audio.schemas import AudioFileResponse
from src.domains.audio.services import AudioService
from src.domains.user.schemas import UserResponse

router = APIRouter()

@router.post("/", response_model=AudioFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_audio(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    audio_service: AudioService = Depends(),
):
    """Upload a new audio file."""
    try:
        # Проверка размера файла
        if file.size and file.size > 200 * 1024 * 1024:  # 200 MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large. Maximum size is 200 MB.",
            )
        
        # Проверка формата файла
        filename = file.filename or ""
        if not any(filename.lower().endswith(ext) for ext in [".mp3", ".wav", ".ogg", ".m4a", ".webm"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Supported formats: mp3, wav, ogg, m4a, webm.",
            )
        
        # Сохранение файла
        audio_file = await audio_service.save_audio_file(
            file=file,
            user_id=current_user.id,
            db=db,
        )
        
        return audio_file
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.get("/", response_model=dict)
async def list_audio_files(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    audio_service: AudioService = Depends(),
):
    """Get a list of audio files."""
    audio_files, total = await audio_service.get_audio_files(
        user_id=current_user.id,
        page=page,
        limit=limit,
        db=db,
    )
    
    return {
        "items": audio_files,
        "total": total,
        "page": page,
        "limit": limit,
    }

@router.get("/{audio_id}", response_model=AudioFileResponse)
async def get_audio_file(
    audio_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    audio_service: AudioService = Depends(),
):
    """Get information about a specific audio file."""
    audio_file = await audio_service.get_audio_file(
        audio_id=audio_id,
        user_id=current_user.id,
        db=db,
    )
    
    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio file with ID {audio_id} not found.",
        )
    
    return audio_file

@router.delete("/{audio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audio_file(
    audio_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    audio_service: AudioService = Depends(),
):
    """Delete a specific audio file."""
    audio_file = await audio_service.get_audio_file(
        audio_id=audio_id,
        user_id=current_user.id,
        db=db,
    )
    
    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio file with ID {audio_id} not found.",
        )
    
    await audio_service.delete_audio_file(
        audio_id=audio_id,
        user_id=current_user.id,
        db=db,
    )
```

**Роутер для проверки здоровья:**
```python
# src/application/api/routes/health.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.api.dependencies import get_current_user, get_db
from src.domains.user.schemas import UserResponse

router = APIRouter()

@router.get("/")
async def health_check():
    """Check the health of the API."""
    return {
        "status": "ok",
        "version": "1.0.0",
    }

@router.get("/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Check the health of all API components."""
    # Проверка базы данных
    try:
        await db.execute("SELECT 1")
        db_status = "ok"
    except Exception as e:
        db_status = "down"
    
    # В реальном приложении здесь будут проверки других компонентов
    
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "version": "1.0.0",
        "components": {
            "database": {
                "status": db_status,
            },
            # Другие компоненты
        },
    }
```

#### Схемы данных/API

**Структура API:**
```
/auth
  /token - Получение JWT токена
  /me - Получение информации о текущем пользователе

/audio
  / - Загрузка и получение списка аудиофайлов
  /{audio_id} - Получение информации и удаление аудиофайла

/transcription
  / - Создание и получение списка задач транскрипции
  /{transcription_id} - Получение информации о задаче транскрипции

/diarization
  / - Создание задачи диаризации
  /{diarization_id} - Получение информации о задаче диаризации

/export
  /{transcription_id} - Экспорт результатов транскрипции в различных форматах

/health
  / - Базовая проверка здоровья API
  /detailed - Детальная проверка здоровья всех компонентов API
```

**Структура данных:**
```
AudioFile
  - id: UUID
  - user_id: int
  - original_filename: string
  - format: enum (mp3, wav, ogg, m4a, webm)
  - size_bytes: int
  - duration_seconds: float
  - is_valid: boolean
  - created_at: datetime
  - updated_at: datetime

Transcription
  - id: UUID
  - audio_id: UUID
  - user_id: int
  - model: enum (whisper-large-v3, whisper-turbo)
  - status: enum (pending, in_progress, completed, failed)
  - language: string
  - progress: int
  - error_message: string
  - created_at: datetime
  - updated_at: datetime
  - segments: TranscriptionSegment[]

TranscriptionSegment
  - id: UUID
  - transcription_id: UUID
  - start_time: float
  - end_time: float
  - text: string
  - confidence: float
  - created_at: datetime

Diarization
  - id: UUID
  - audio_id: UUID
  - user_id: int
  - status: enum (pending, in_progress, completed, failed)
  - num_speakers: int
  - progress: int
  - error_message: string
  - created_at: datetime
  - updated_at: datetime
  - segments: DiarizationSegment[]

DiarizationSegment
  - id: UUID
  - diarization_id: UUID
  - speaker_id: int
  - start_time: float
  - end_time: float
  - confidence: float
  - created_at: datetime
```

### 2. Практическая секция

#### Пошаговые инструкции

1. **Создание OpenAPI спецификации:**
   - Создайте файл `openapi.yaml` в корне проекта
   - Определите все необходимые эндпоинты и схемы данных
   - Добавьте описания, примеры и документацию для каждого эндпоинта

2. **Создание Pydantic моделей:**
   - Создайте файлы с моделями для каждого домена (audio, transcription, diarization, export)
   - Определите базовые модели, модели для создания, обновления и ответов
   - Добавьте валидацию данных и документацию

3. **Настройка FastAPI приложения:**
   - Создайте основной файл приложения
   - Настройте middleware для логирования и обработки ошибок
   - Настройте документацию API (Swagger UI, ReDoc)

4. **Создание роутеров:**
   - Создайте отдельные роутеры для каждого домена
   - Реализуйте базовые эндпоинты для каждого роутера
   - Добавьте зависимости для аутентификации и доступа к базе данных

5. **Настройка аутентификации:**
   - Реализуйте эндпоинты для аутентификации
   - Настройте JWT токены для защиты API
   - Добавьте middleware для проверки токенов

6. **Тестирование API:**
   - Запустите API локально
   - Проверьте работу всех эндпоинтов через Swagger UI
   - Напишите автоматические тесты для API

#### Частые ошибки (Common Pitfalls)

1. **Проблемы с OpenAPI спецификацией:**
   - Неправильное определение схем данных
   - Отсутствие описаний и примеров
   - Несоответствие спецификации и реализации

2. **Проблемы с Pydantic моделями:**
   - Неправильная валидация данных
   - Отсутствие документации
   - Несоответствие моделей и схемы базы данных

3. **Проблемы с FastAPI:**
   - Неправильная настройка зависимостей
   - Проблемы с асинхронными обработчиками
   - Отсутствие обработки ошибок

#### Советы по оптимизации (Performance Tips)

1. **Оптимизация API:**
   - Используйте пагинацию для больших наборов данных
   - Применяйте кэширование для часто запрашиваемых данных
   - Используйте асинхронные обработчики для длительных операций

2. **Оптимизация Pydantic:**
   - Используйте `from_attributes=True` для преобразования ORM моделей
   - Применяйте `exclude_unset=True` для частичных обновлений
   - Используйте `alias_generator` для преобразования имен полей

3. **Оптимизация FastAPI:**
   - Используйте `response_model_exclude_unset=True` для уменьшения размера ответов
   - Применяйте `BackgroundTasks` для асинхронной обработки
   - Используйте `Depends` для инъекции зависимостей

### 3. Валидационная секция

#### Чек-лист для самопроверки

- [ ] OpenAPI спецификация создана и соответствует требованиям
- [ ] Pydantic модели созданы для всех доменов
- [ ] FastAPI приложение настроено и запускается
- [ ] Роутеры созданы для всех доменов
- [ ] Аутентификация настроена и работает
- [ ] Документация API доступна через Swagger UI и ReDoc
- [ ] Базовые эндпоинты реализованы и работают
- [ ] Обработка ошибок настроена
- [ ] Логирование запросов настроено
- [ ] Тесты для API написаны и проходят

#### Автоматизированные тесты

```python
# tests/application/api/test_health.py
import pytest
from fastapi.testclient import TestClient

from src.application.api.main import app


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "version" in response.json()


def test_root(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()
    assert "version" in response.json()
    assert "docs" in response.json()
    assert "redoc" in response.json()


# tests/application/api/test_auth.py
import pytest
from fastapi.testclient import TestClient

from src.application.api.main import app


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


def test_login(client):
    """Test the login endpoint."""
    response = client.post(
        "/auth/token",
        data={"username": "test", "password": "test"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    """Test the login endpoint with invalid credentials."""
    response = client.post(
        "/auth/token",
        data={"username": "test", "password": "wrong"},
    )
    assert response.status_code == 401


def test_get_current_user(client):
    """Test the get current user endpoint."""
    # First, get a token
    response = client.post(
        "/auth/token",
        data={"username": "test", "password": "test"},
    )
    token = response.json()["access_token"]
    
    # Then, use the token to get the current user
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "test"
```

#### Критерии для ручного тестирования

1. **Проверка документации API:**
   - Откройте Swagger UI по адресу `/docs`
   - Убедитесь, что все эндпоинты и схемы данных отображаются корректно
   - Проверьте, что описания и примеры присутствуют

2. **Проверка аутентификации:**
   - Попробуйте получить токен с правильными учетными данными
   - Попробуйте получить токен с неправильными учетными данными
   - Попробуйте получить доступ к защищенному эндпоинту без токена
   - Попробуйте получить доступ к защищенному эндпоинту с токеном

3. **Проверка эндпоинтов для аудиофайлов:**
   - Загрузите аудиофайл
   - Получите список аудиофайлов
   - Получите информацию о конкретном аудиофайле
   - Удалите аудиофайл

4. **Проверка эндпоинтов для транскрипции:**
   - Создайте задачу транскрипции
   - Получите список задач транскрипции
   - Получите информацию о конкретной задаче транскрипции

5. **Проверка эндпоинтов для диаризации:**
   - Создайте задачу диаризации
   - Получите информацию о конкретной задаче диаризации

6. **Проверка эндпоинтов для экспорта:**
   - Экспортируйте результаты транскрипции в различных форматах

## Вопросы к постановщику задачи
1. Какие дополнительные эндпоинты нужно добавить в API?
2. Требуется ли поддержка версионирования API?
3. Какие ограничения по скорости запросов (rate limiting) нужно реализовать?
4. Требуется ли поддержка WebSockets для отслеживания прогресса обработки в реальном времени?
5. Какие дополнительные форматы экспорта нужно поддерживать помимо указанных (DOCX, SRT, JSON, TXT)?