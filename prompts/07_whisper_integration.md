# Фаза 2, День 2. Интеграция с Whisper

## Цель (Definition of Done)
- Настроена интеграция с моделями OpenAI Whisper (large-v3 и turbo)
- Реализован сервис для транскрипции аудио с использованием Whisper
- Настроена обработка временных меток с точностью до 1 секунды
- Реализована поддержка русского и английского языков
- Настроено автоматическое определение языка
- Реализована оптимизация производительности и кэширование моделей
- Написаны тесты для проверки функциональности транскрипции

## Ссылки на документацию
- [OpenAI Whisper Documentation](https://github.com/openai/whisper)
- [Faster-Whisper Documentation](https://github.com/guillaumekln/faster-whisper)
- [HuggingFace Transformers Documentation](https://huggingface.co/docs/transformers/index)
- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)
- [CUDA Documentation](https://docs.nvidia.com/cuda/index.html)

---

### 1. Техническая секция

#### Описание
В этом задании необходимо реализовать интеграцию с моделями OpenAI Whisper для транскрипции аудиофайлов. Whisper - это мощная модель для автоматического распознавания речи (ASR), которая поддерживает множество языков и обеспечивает высокое качество транскрипции. Мы будем использовать две версии модели: large-v3 для высокого качества и turbo для быстрой обработки.

Основные компоненты:
1. **Загрузка и кэширование моделей** - эффективная загрузка моделей Whisper и их кэширование
2. **Транскрипция аудио** - преобразование аудио в текст с временными метками
3. **Определение языка** - автоматическое определение языка аудио
4. **Оптимизация производительности** - настройка параметров для оптимальной работы моделей
5. **Обработка результатов** - структурирование результатов транскрипции для дальнейшего использования

#### Примеры кода

**Сервис для транскрипции с использованием Whisper:**
```python
# src/domains/transcription/services/whisper_service.py
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import structlog
import torch
from faster_whisper import WhisperModel

from src.config.settings import config
from src.domains.audio.entities import AudioFile
from src.domains.transcription.entities import Transcription, TranscriptionModel, TranscriptionSegment, TranscriptionStatus
from src.domains.transcription.exceptions import TranscriptionError

logger = structlog.get_logger()


class WhisperService:
    """Service for transcribing audio using Whisper models."""

    # Mapping of model names to their HuggingFace identifiers
    MODEL_MAPPING = {
        TranscriptionModel.WHISPER_LARGE_V3: "large-v3",
        TranscriptionModel.WHISPER_TURBO: "medium",  # Using medium as a proxy for turbo
    }

    # Supported languages with their codes
    SUPPORTED_LANGUAGES = {
        "ru": "Russian",
        "en": "English",
    }

    def __init__(self):
        """Initialize the Whisper service."""
        self.models: Dict[str, WhisperModel] = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "float32"
        
        # Create model cache directory if it doesn't exist
        os.makedirs(config.MODEL_CACHE_DIR, exist_ok=True)
        
        logger.info(
            "Initialized WhisperService",
            device=self.device,
            compute_type=self.compute_type,
            model_cache_dir=str(config.MODEL_CACHE_DIR),
        )

    async def transcribe(
        self,
        audio_path: Path,
        model_name: TranscriptionModel = TranscriptionModel.WHISPER_LARGE_V3,
        language: Optional[str] = None,
        task: str = "transcribe",
        verbose: bool = False,
    ) -> Tuple[List[TranscriptionSegment], Optional[str]]:
        """Transcribe audio file using Whisper.

        Args:
            audio_path: Path to the audio file.
            model_name: Whisper model to use.
            language: Language code (e.g., "en", "ru"). If None, language will be auto-detected.
            task: Task to perform ("transcribe" or "translate").
            verbose: Whether to print progress information.

        Returns:
            Tuple of (list of TranscriptionSegment, detected_language).

        Raises:
            TranscriptionError: If there's an error during transcription.
        """
        try:
            # Load model if not already loaded
            model = await self._get_model(model_name)
            
            # Log transcription start
            logger.info(
                "Starting transcription",
                audio_path=str(audio_path),
                model=model_name,
                language=language,
                task=task,
            )
            
            # Perform transcription
            segments, info = model.transcribe(
                str(audio_path),
                language=language,
                task=task,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
            )
            
            # Process segments
            transcription_segments = []
            for segment in segments:
                # Create TranscriptionSegment
                transcription_segment = TranscriptionSegment(
                    start_time=segment.start,
                    end_time=segment.end,
                    text=segment.text.strip(),
                    confidence=float(segment.avg_logprob),
                )
                transcription_segments.append(transcription_segment)
            
            # Get detected language
            detected_language = info.language
            
            # Log transcription completion
            logger.info(
                "Transcription completed",
                audio_path=str(audio_path),
                model=model_name,
                detected_language=detected_language,
                num_segments=len(transcription_segments),
            )
            
            return transcription_segments, detected_language
        except Exception as e:
            logger.error(
                "Error during transcription",
                audio_path=str(audio_path),
                model=model_name,
                error=str(e),
                exc_info=True,
            )
            raise TranscriptionError(f"Error during transcription: {str(e)}")

    async def detect_language(
        self,
        audio_path: Path,
        model_name: TranscriptionModel = TranscriptionModel.WHISPER_TURBO,
    ) -> str:
        """Detect language of audio file.

        Args:
            audio_path: Path to the audio file.
            model_name: Whisper model to use.

        Returns:
            Detected language code.

        Raises:
            TranscriptionError: If there's an error during language detection.
        """
        try:
            # Load model if not already loaded
            model = await self._get_model(model_name)
            
            # Log language detection start
            logger.info(
                "Starting language detection",
                audio_path=str(audio_path),
                model=model_name,
            )
            
            # Detect language
            _, info = model.transcribe(
                str(audio_path),
                language=None,
                task="transcribe",
                vad_filter=True,
                duration=30.0,  # Only use first 30 seconds for language detection
            )
            
            detected_language = info.language
            
            # Log language detection completion
            logger.info(
                "Language detection completed",
                audio_path=str(audio_path),
                model=model_name,
                detected_language=detected_language,
            )
            
            return detected_language
        except Exception as e:
            logger.error(
                "Error during language detection",
                audio_path=str(audio_path),
                model=model_name,
                error=str(e),
                exc_info=True,
            )
            raise TranscriptionError(f"Error during language detection: {str(e)}")

    async def _get_model(self, model_name: TranscriptionModel) -> WhisperModel:
        """Get Whisper model, loading it if necessary.

        Args:
            model_name: Whisper model to use.

        Returns:
            WhisperModel instance.

        Raises:
            TranscriptionError: If there's an error loading the model.
        """
        try:
            # Check if model is already loaded
            if model_name in self.models:
                return self.models[model_name]
            
            # Get model identifier
            model_id = self.MODEL_MAPPING.get(model_name)
            if not model_id:
                raise TranscriptionError(f"Unknown model: {model_name}")
            
            # Log model loading
            logger.info(
                "Loading Whisper model",
                model=model_name,
                model_id=model_id,
                device=self.device,
                compute_type=self.compute_type,
            )
            
            # Load model
            model = WhisperModel(
                model_id,
                device=self.device,
                compute_type=self.compute_type,
                download_root=str(config.MODEL_CACHE_DIR),
            )
            
            # Cache model
            self.models[model_name] = model
            
            # Log model loading completion
            logger.info(
                "Whisper model loaded",
                model=model_name,
                model_id=model_id,
            )
            
            return model
        except Exception as e:
            logger.error(
                "Error loading Whisper model",
                model=model_name,
                error=str(e),
                exc_info=True,
            )
            raise TranscriptionError(f"Error loading Whisper model: {str(e)}")
```

**Сервис для управления транскрипциями:**
```python
# src/domains/transcription/services/transcription_service.py
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.audio.entities import AudioFile
from src.domains.audio.repositories import AudioRepository
from src.domains.audio.services.audio_processor import AudioProcessor
from src.domains.transcription.entities import Transcription, TranscriptionModel, TranscriptionSegment, TranscriptionStatus
from src.domains.transcription.exceptions import TranscriptionError
from src.domains.transcription.repositories import TranscriptionRepository, TranscriptionSegmentRepository
from src.domains.transcription.services.whisper_service import WhisperService

logger = structlog.get_logger()


class TranscriptionService:
    """Service for managing transcriptions."""

    def __init__(
        self,
        transcription_repository: TranscriptionRepository,
        transcription_segment_repository: TranscriptionSegmentRepository,
        audio_repository: AudioRepository,
        audio_processor: AudioProcessor,
        whisper_service: WhisperService,
    ):
        """Initialize the transcription service.

        Args:
            transcription_repository: Repository for transcriptions.
            transcription_segment_repository: Repository for transcription segments.
            audio_repository: Repository for audio files.
            audio_processor: Service for processing audio files.
            whisper_service: Service for transcribing audio.
        """
        self.transcription_repository = transcription_repository
        self.transcription_segment_repository = transcription_segment_repository
        self.audio_repository = audio_repository
        self.audio_processor = audio_processor
        self.whisper_service = whisper_service
        self.logger = structlog.get_logger()

    async def create_transcription(
        self,
        audio_id: str,
        user_id: int,
        model: TranscriptionModel = TranscriptionModel.WHISPER_LARGE_V3,
        language: Optional[str] = None,
        auto_detect_language: bool = True,
        db: AsyncSession = None,
    ) -> Transcription:
        """Create a new transcription task.

        Args:
            audio_id: ID of the audio file to transcribe.
            user_id: ID of the user who created the task.
            model: Transcription model to use.
            language: Language code (e.g., "en", "ru"). If None and auto_detect_language is False,
                language will be auto-detected.
            auto_detect_language: Whether to auto-detect the language.
            db: Database session.

        Returns:
            Created transcription entity.

        Raises:
            TranscriptionError: If there's an error creating the transcription.
        """
        try:
            # Get audio file
            audio_file = await self.audio_repository.get_by_id(audio_id, db=db)
            if not audio_file:
                raise TranscriptionError(f"Audio file with ID {audio_id} not found")
            
            # Check if audio file belongs to the user
            if audio_file.user_id != user_id:
                raise TranscriptionError(f"Audio file with ID {audio_id} does not belong to user {user_id}")
            
            # Create transcription entity
            transcription_id = str(uuid.uuid4())
            transcription = Transcription(
                id=transcription_id,
                audio_id=audio_id,
                user_id=user_id,
                model=model,
                language=language,
                status=TranscriptionStatus.PENDING,
                progress=0,
            )
            
            # Save transcription to database
            transcription = await self.transcription_repository.create(transcription, db=db)
            
            # Log transcription creation
            self.logger.info(
                "Transcription created",
                transcription_id=transcription_id,
                audio_id=audio_id,
                user_id=user_id,
                model=model,
                language=language,
                auto_detect_language=auto_detect_language,
            )
            
            return transcription
        except Exception as e:
            self.logger.error(
                "Error creating transcription",
                audio_id=audio_id,
                user_id=user_id,
                model=model,
                error=str(e),
                exc_info=True,
            )
            raise TranscriptionError(f"Error creating transcription: {str(e)}")

    async def process_transcription(
        self,
        transcription_id: str,
        db: AsyncSession = None,
    ) -> Transcription:
        """Process a transcription task.

        Args:
            transcription_id: ID of the transcription to process.
            db: Database session.

        Returns:
            Updated transcription entity.

        Raises:
            TranscriptionError: If there's an error processing the transcription.
        """
        try:
            # Get transcription
            transcription = await self.transcription_repository.get_by_id(transcription_id, db=db)
            if not transcription:
                raise TranscriptionError(f"Transcription with ID {transcription_id} not found")
            
            # Check if transcription is already completed or failed
            if transcription.status in [TranscriptionStatus.COMPLETED, TranscriptionStatus.FAILED]:
                return transcription
            
            # Update status to in progress
            transcription.status = TranscriptionStatus.IN_PROGRESS
            transcription.progress = 10
            transcription = await self.transcription_repository.update(transcription, db=db)
            
            # Get audio file
            audio_file = await self.audio_repository.get_by_id(transcription.audio_id, db=db)
            if not audio_file:
                raise TranscriptionError(f"Audio file with ID {transcription.audio_id} not found")
            
            # Convert audio to WAV if needed
            if audio_file.format != "wav":
                wav_path = await self.audio_processor.convert_to_wav(audio_file.path)
                transcription.progress = 20
                transcription = await self.transcription_repository.update(transcription, db=db)
            else:
                wav_path = audio_file.path
            
            # Normalize volume
            normalized_path = await self.audio_processor.normalize_volume(wav_path)
            transcription.progress = 30
            transcription = await self.transcription_repository.update(transcription, db=db)
            
            # Auto-detect language if needed
            if not transcription.language:
                language = await self.whisper_service.detect_language(
                    normalized_path,
                    model_name=TranscriptionModel.WHISPER_TURBO,
                )
                transcription.language = language
                transcription.progress = 40
                transcription = await self.transcription_repository.update(transcription, db=db)
            
            # Transcribe audio
            segments, detected_language = await self.whisper_service.transcribe(
                normalized_path,
                model_name=transcription.model,
                language=transcription.language,
            )
            
            # Update language if it was auto-detected
            if not transcription.language:
                transcription.language = detected_language
            
            # Save segments to database
            for segment in segments:
                segment.transcription_id = transcription_id
                await self.transcription_segment_repository.create(segment, db=db)
            
            # Update transcription status
            transcription.status = TranscriptionStatus.COMPLETED
            transcription.progress = 100
            transcription = await self.transcription_repository.update(transcription, db=db)
            
            # Log transcription completion
            self.logger.info(
                "Transcription completed",
                transcription_id=transcription_id,
                audio_id=transcription.audio_id,
                user_id=transcription.user_id,
                model=transcription.model,
                language=transcription.language,
                num_segments=len(segments),
            )
            
            return transcription
        except Exception as e:
            # Update transcription status to failed
            if transcription:
                transcription.status = TranscriptionStatus.FAILED
                transcription.error_message = str(e)
                await self.transcription_repository.update(transcription, db=db)
            
            self.logger.error(
                "Error processing transcription",
                transcription_id=transcription_id,
                error=str(e),
                exc_info=True,
            )
            raise TranscriptionError(f"Error processing transcription: {str(e)}")

    async def get_transcription(
        self,
        transcription_id: str,
        include_segments: bool = True,
        db: AsyncSession = None,
    ) -> Optional[Transcription]:
        """Get a transcription by ID.

        Args:
            transcription_id: ID of the transcription to get.
            include_segments: Whether to include transcription segments.
            db: Database session.

        Returns:
            Transcription entity, or None if not found.
        """
        try:
            # Get transcription
            transcription = await self.transcription_repository.get_by_id(transcription_id, db=db)
            if not transcription:
                return None
            
            # Get segments if requested
            if include_segments and transcription.status == TranscriptionStatus.COMPLETED:
                segments = await self.transcription_segment_repository.get_by_transcription_id(
                    transcription_id, db=db
                )
                transcription.segments = segments
            
            return transcription
        except Exception as e:
            self.logger.error(
                "Error getting transcription",
                transcription_id=transcription_id,
                error=str(e),
                exc_info=True,
            )
            return None

    async def get_transcriptions_by_user(
        self,
        user_id: int,
        page: int = 1,
        limit: int = 10,
        status: Optional[TranscriptionStatus] = None,
        db: AsyncSession = None,
    ) -> Tuple[List[Transcription], int]:
        """Get transcriptions by user ID.

        Args:
            user_id: ID of the user.
            page: Page number.
            limit: Number of items per page.
            status: Filter by status.
            db: Database session.

        Returns:
            Tuple of (list of transcriptions, total count).
        """
        try:
            # Get transcriptions
            transcriptions, total = await self.transcription_repository.get_by_user_id(
                user_id, page=page, limit=limit, status=status, db=db
            )
            
            return transcriptions, total
        except Exception as e:
            self.logger.error(
                "Error getting transcriptions by user",
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            return [], 0

    async def delete_transcription(
        self,
        transcription_id: str,
        user_id: int,
        db: AsyncSession = None,
    ) -> bool:
        """Delete a transcription.

        Args:
            transcription_id: ID of the transcription to delete.
            user_id: ID of the user who owns the transcription.
            db: Database session.

        Returns:
            True if the transcription was deleted, False otherwise.
        """
        try:
            # Get transcription
            transcription = await self.transcription_repository.get_by_id(transcription_id, db=db)
            if not transcription:
                return False
            
            # Check if transcription belongs to the user
            if transcription.user_id != user_id:
                return False
            
            # Delete segments
            await self.transcription_segment_repository.delete_by_transcription_id(transcription_id, db=db)
            
            # Delete transcription
            await self.transcription_repository.delete(transcription_id, db=db)
            
            # Log transcription deletion
            self.logger.info(
                "Transcription deleted",
                transcription_id=transcription_id,
                user_id=user_id,
            )
            
            return True
        except Exception as e:
            self.logger.error(
                "Error deleting transcription",
                transcription_id=transcription_id,
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            return False
```

**Исключения для транскрипции:**
```python
# src/domains/transcription/exceptions.py
class TranscriptionError(Exception):
    """Base exception for transcription errors."""
    pass


class ModelLoadingError(TranscriptionError):
    """Exception raised when there's an error loading a model."""
    pass


class LanguageDetectionError(TranscriptionError):
    """Exception raised when there's an error detecting language."""
    pass


class UnsupportedLanguageError(TranscriptionError):
    """Exception raised when the language is not supported."""
    pass
```

**Сущности для транскрипции:**
```python
# src/domains/transcription/entities.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID


class TranscriptionModel(str, Enum):
    """Enum for transcription models."""
    WHISPER_LARGE_V3 = "whisper-large-v3"
    WHISPER_TURBO = "whisper-turbo"


class TranscriptionStatus(str, Enum):
    """Enum for transcription status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TranscriptionSegment:
    """Entity representing a transcription segment."""
    start_time: float
    end_time: float
    text: str
    confidence: float
    id: Optional[str] = None
    transcription_id: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class Transcription:
    """Entity representing a transcription."""
    id: str
    audio_id: str
    user_id: int
    model: TranscriptionModel
    status: TranscriptionStatus
    language: Optional[str] = None
    progress: int = 0
    error_message: Optional[str] = None
    segments: List[TranscriptionSegment] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

**Интеграция с FastAPI для транскрипции:**
```python
# src/application/api/routes/transcription.py
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.api.dependencies import get_current_user, get_db
from src.domains.transcription.entities import TranscriptionModel, TranscriptionStatus
from src.domains.transcription.exceptions import TranscriptionError
from src.domains.transcription.schemas import TranscriptionCreate, TranscriptionResponse
from src.domains.transcription.services.transcription_service import TranscriptionService
from src.domains.user.schemas import UserResponse

router = APIRouter()


@router.post("/", response_model=TranscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_transcription(
    transcription_create: TranscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    transcription_service: TranscriptionService = Depends(),
):
    """Create a new transcription task."""
    try:
        transcription = await transcription_service.create_transcription(
            audio_id=str(transcription_create.audio_id),
            user_id=current_user.id,
            model=transcription_create.model,
            language=transcription_create.language,
            auto_detect_language=transcription_create.auto_detect_language,
            db=db,
        )
        
        # Start processing in background
        # In a real application, this would be handled by a task queue
        # For simplicity, we're just returning the created transcription
        
        return transcription
    except TranscriptionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating transcription: {str(e)}",
        )


@router.get("/", response_model=dict)
async def list_transcriptions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[TranscriptionStatus] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    transcription_service: TranscriptionService = Depends(),
):
    """Get a list of transcription tasks."""
    transcriptions, total = await transcription_service.get_transcriptions_by_user(
        user_id=current_user.id,
        page=page,
        limit=limit,
        status=status_filter,
        db=db,
    )
    
    return {
        "items": transcriptions,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/{transcription_id}", response_model=TranscriptionResponse)
async def get_transcription(
    transcription_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    transcription_service: TranscriptionService = Depends(),
):
    """Get information about a specific transcription task."""
    transcription = await transcription_service.get_transcription(
        transcription_id=str(transcription_id),
        include_segments=True,
        db=db,
    )
    
    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcription with ID {transcription_id} not found",
        )
    
    if transcription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Transcription with ID {transcription_id} does not belong to user {current_user.id}",
        )
    
    return transcription


@router.delete("/{transcription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transcription(
    transcription_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    transcription_service: TranscriptionService = Depends(),
):
    """Delete a specific transcription task."""
    success = await transcription_service.delete_transcription(
        transcription_id=str(transcription_id),
        user_id=current_user.id,
        db=db,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcription with ID {transcription_id} not found or does not belong to user {current_user.id}",
        )
```

#### Схемы данных/API

**Структура транскрипции:**
```
1. Пользователь создает задачу транскрипции для аудиофайла
2. Система проверяет, что аудиофайл существует и принадлежит пользователю
3. Система создает запись о транскрипции в базе данных со статусом "pending"
4. Система отправляет задачу в очередь для асинхронной обработки
5. Обработчик задач получает задачу и начинает обработку
6. Система обновляет статус транскрипции на "in_progress"
7. Система конвертирует аудиофайл в WAV, если необходимо
8. Система нормализует громкость аудио
9. Система определяет язык аудио, если не указан
10. Система выполняет транскрипцию с использованием выбранной модели Whisper
11. Система сохраняет сегменты транскрипции в базе данных
12. Система обновляет статус транскрипции на "completed"
13. Пользователь может получить результаты транскрипции через API
```

**Диаграмма последовательности транскрипции:**
```
User -> API: Create transcription task
API -> TranscriptionService: create_transcription()
TranscriptionService -> Database: Save transcription with status "pending"
Database -> TranscriptionService: Saved transcription
TranscriptionService -> API: Transcription entity
API -> User: Transcription response

TaskQueue -> TranscriptionService: process_transcription()
TranscriptionService -> Database: Update status to "in_progress"
TranscriptionService -> AudioProcessor: convert_to_wav() if needed
AudioProcessor -> TranscriptionService: WAV file path
TranscriptionService -> AudioProcessor: normalize_volume()
AudioProcessor -> TranscriptionService: Normalized file path

alt language not specified
    TranscriptionService -> WhisperService: detect_language()
    WhisperService -> TranscriptionService: Detected language
    TranscriptionService -> Database: Update language
end

TranscriptionService -> WhisperService: transcribe()
WhisperService -> TranscriptionService: Transcription segments
TranscriptionService -> Database: Save segments
TranscriptionService -> Database: Update status to "completed"

User -> API: Get transcription
API -> TranscriptionService: get_transcription()
TranscriptionService -> Database: Get transcription and segments
Database -> TranscriptionService: Transcription with segments
TranscriptionService -> API: Transcription entity
API -> User: Transcription response with segments
```

### 2. Практическая секция

#### Пошаговые инструкции

1. **Настройка зависимостей:**
   - Установите необходимые пакеты: faster-whisper, torch, numpy
   - Настройте CUDA, если доступно, для ускорения обработки
   - Настройте пути для кэширования моделей

2. **Реализация сервиса Whisper:**
   - Создайте класс WhisperService для работы с моделями Whisper
   - Реализуйте загрузку и кэширование моделей
   - Добавьте методы для транскрипции и определения языка

3. **Реализация сервиса транскрипции:**
   - Создайте класс TranscriptionService для управления транскрипциями
   - Реализуйте методы для создания, обработки и получения транскрипций
   - Добавьте интеграцию с сервисом Whisper

4. **Реализация репозиториев:**
   - Создайте репозитории для работы с транскрипциями и сегментами
   - Реализуйте методы CRUD для работы с базой данных
   - Добавьте методы для получения транскрипций по пользователю

5. **Реализация API эндпоинтов:**
   - Создайте роутер для работы с транскрипциями
   - Реализуйте эндпоинты для создания, получения и удаления транскрипций
   - Добавьте валидацию и обработку ошибок

6. **Оптимизация производительности:**
   - Настройте параметры моделей для оптимальной производительности
   - Реализуйте кэширование моделей для ускорения загрузки
   - Добавьте асинхронную обработку для длительных операций

7. **Написание тестов:**
   - Создайте тесты для сервиса Whisper
   - Добавьте тесты для сервиса транскрипции
   - Реализуйте тесты для API эндпоинтов

#### Частые ошибки (Common Pitfalls)

1. **Проблемы с моделями Whisper:**
   - Неправильные пути к моделям
   - Недостаточно памяти для загрузки больших моделей
   - Неправильные параметры для транскрипции

2. **Проблемы с CUDA:**
   - Несовместимость версий CUDA и PyTorch
   - Недостаточно видеопамяти для моделей
   - Неправильная настройка CUDA для использования GPU

3. **Проблемы с обработкой аудио:**
   - Неподдерживаемые форматы аудио
   - Слишком большие файлы, вызывающие проблемы с памятью
   - Низкое качество аудио, влияющее на точность транскрипции

4. **Проблемы с асинхронной обработкой:**
   - Блокировка основного потока при длительных операциях
   - Утечки ресурсов при асинхронной обработке
   - Неправильная обработка ошибок в асинхронных задачах

#### Советы по оптимизации (Performance Tips)

1. **Оптимизация моделей Whisper:**
   - Используйте модель turbo для быстрой обработки, когда качество не критично
   - Применяйте квантизацию моделей для уменьшения использования памяти
   - Используйте кэширование моделей для ускорения загрузки

2. **Оптимизация GPU:**
   - Используйте CUDA для ускорения обработки на GPU
   - Настройте параметры batch_size для оптимального использования GPU
   - Освобождайте память GPU после обработки больших файлов

3. **Оптимизация обработки аудио:**
   - Разбивайте большие файлы на сегменты для параллельной обработки
   - Используйте детектирование тишины для пропуска пустых участков
   - Применяйте предварительную обработку аудио для улучшения качества транскрипции

### 3. Валидационная секция

#### Чек-лист для самопроверки

- [ ] Модели Whisper (large-v3 и turbo) успешно интегрированы
- [ ] Реализован сервис для транскрипции аудио
- [ ] Настроена обработка временных меток
- [ ] Реализована поддержка русского и английского языков
- [ ] Настроено автоматическое определение языка
- [ ] Реализована оптимизация производительности
- [ ] Настроено кэширование моделей
- [ ] Написаны тесты для проверки функциональности
- [ ] Обработка ошибок реализована и тестируется
- [ ] Код соответствует PEP 8 и включает типизацию
- [ ] Документация к коду добавлена и актуальна

#### Автоматизированные тесты

```python
# tests/domains/transcription/services/test_whisper_service.py
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import torch

from src.domains.transcription.entities import TranscriptionModel
from src.domains.transcription.exceptions import TranscriptionError
from src.domains.transcription.services.whisper_service import WhisperService


@pytest.fixture
def whisper_service():
    """Create a WhisperService instance."""
    with patch("src.domains.transcription.services.whisper_service.WhisperModel") as mock_model:
        # Mock the WhisperModel to avoid actual model loading
        instance = mock_model.return_value
        instance.transcribe.return_value = (
            [
                MagicMock(
                    start=0.0,
                    end=2.0,
                    text="Hello, world!",
                    avg_logprob=-0.1,
                ),
                MagicMock(
                    start=2.0,
                    end=4.0,
                    text="This is a test.",
                    avg_logprob=-0.2,
                ),
            ],
            MagicMock(language="en"),
        )
        
        service = WhisperService()
        yield service


@pytest.fixture
def sample_audio_file():
    """Create a sample audio file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        # Create an empty file
        temp_file.write(b"dummy audio data")
        temp_file_path = Path(temp_file.name)
    
    yield temp_file_path
    
    # Clean up
    if temp_file_path.exists():
        temp_file_path.unlink()


@pytest.mark.asyncio
async def test_transcribe(whisper_service, sample_audio_file):
    """Test transcribing audio."""
    segments, language = await whisper_service.transcribe(
        audio_path=sample_audio_file,
        model_name=TranscriptionModel.WHISPER_TURBO,
    )
    
    assert len(segments) == 2
    assert segments[0].text == "Hello, world!"
    assert segments[0].start_time == 0.0
    assert segments[0].end_time == 2.0
    assert segments[0].confidence == -0.1
    
    assert segments[1].text == "This is a test."
    assert segments[1].start_time == 2.0
    assert segments[1].end_time == 4.0
    assert segments[1].confidence == -0.2
    
    assert language == "en"


@pytest.mark.asyncio
async def test_detect_language(whisper_service, sample_audio_file):
    """Test detecting language."""
    language = await whisper_service.detect_language(
        audio_path=sample_audio_file,
        model_name=TranscriptionModel.WHISPER_TURBO,
    )
    
    assert language == "en"


@pytest.mark.asyncio
async def test_get_model(whisper_service):
    """Test getting a model."""
    model = await whisper_service._get_model(TranscriptionModel.WHISPER_TURBO)
    
    assert model is not None
    assert TranscriptionModel.WHISPER_TURBO in whisper_service.models


@pytest.mark.asyncio
async def test_get_model_error(whisper_service):
    """Test error when getting an unknown model."""
    with pytest.raises(TranscriptionError):
        await whisper_service._get_model("unknown_model")


# tests/domains/transcription/services/test_transcription_service.py
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domains.audio.entities import AudioFile, AudioFormat
from src.domains.transcription.entities import Transcription, TranscriptionModel, TranscriptionSegment, TranscriptionStatus
from src.domains.transcription.exceptions import TranscriptionError
from src.domains.transcription.services.transcription_service import TranscriptionService


@pytest.fixture
def transcription_service():
    """Create a TranscriptionService instance with mocked dependencies."""
    transcription_repository = AsyncMock()
    transcription_segment_repository = AsyncMock()
    audio_repository = AsyncMock()
    audio_processor = AsyncMock()
    whisper_service = AsyncMock()
    
    service = TranscriptionService(
        transcription_repository=transcription_repository,
        transcription_segment_repository=transcription_segment_repository,
        audio_repository=audio_repository,
        audio_processor=audio_processor,
        whisper_service=whisper_service,
    )
    
    # Set up mocks
    audio_file = AudioFile(
        id="123e4567-e89b-12d3-a456-426614174000",
        user_id=1,
        original_filename="test.mp3",
        format=AudioFormat.MP3,
        size_bytes=1000,
        duration_seconds=10.0,
        path=Path("/tmp/test.mp3"),
        is_valid=True,
    )
    
    transcription = Transcription(
        id="123e4567-e89b-12d3-a456-426614174001",
        audio_id="123e4567-e89b-12d3-a456-426614174000",
        user_id=1,
        model=TranscriptionModel.WHISPER_LARGE_V3,
        status=TranscriptionStatus.PENDING,
    )
    
    segments = [
        TranscriptionSegment(
            id="123e4567-e89b-12d3-a456-426614174002",
            transcription_id="123e4567-e89b-12d3-a456-426614174001",
            start_time=0.0,
            end_time=2.0,
            text="Hello, world!",
            confidence=0.9,
        ),
        TranscriptionSegment(
            id="123e4567-e89b-12d3-a456-426614174003",
            transcription_id="123e4567-e89b-12d3-a456-426614174001",
            start_time=2.0,
            end_time=4.0,
            text="This is a test.",
            confidence=0.8,
        ),
    ]
    
    audio_repository.get_by_id.return_value = audio_file
    transcription_repository.create.return_value = transcription
    transcription_repository.get_by_id.return_value = transcription
    transcription_repository.update.return_value = transcription
    transcription_segment_repository.get_by_transcription_id.return_value = segments
    
    audio_processor.convert_to_wav.return_value = Path("/tmp/test.wav")
    audio_processor.normalize_volume.return_value = Path("/tmp/test_normalized.wav")
    
    whisper_service.detect_language.return_value = "en"
    whisper_service.transcribe.return_value = (segments, "en")
    
    # Add service to the fixture
    service.audio_repository = audio_repository
    service.transcription_repository = transcription_repository
    service.transcription_segment_repository = transcription_segment_repository
    service.audio_processor = audio_processor
    service.whisper_service = whisper_service
    
    return service


@pytest.mark.asyncio
async def test_create_transcription(transcription_service):
    """Test creating a transcription."""
    transcription = await transcription_service.create_transcription(
        audio_id="123e4567-e89b-12d3-a456-426614174000",
        user_id=1,
        model=TranscriptionModel.WHISPER_LARGE_V3,
        db=None,
    )
    
    assert transcription is not None
    assert transcription.audio_id == "123e4567-e89b-12d3-a456-426614174000"
    assert transcription.user_id == 1
    assert transcription.model == TranscriptionModel.WHISPER_LARGE_V3
    assert transcription.status == TranscriptionStatus.PENDING
    
    transcription_service.audio_repository.get_by_id.assert_called_once_with(
        "123e4567-e89b-12d3-a456-426614174000", db=None
    )
    transcription_service.transcription_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_transcription_audio_not_found(transcription_service):
    """Test error when creating a transcription with non-existent audio."""
    transcription_service.audio_repository.get_by_id.return_value = None
    
    with pytest.raises(TranscriptionError):
        await transcription_service.create_transcription(
            audio_id="non-existent",
            user_id=1,
            model=TranscriptionModel.WHISPER_LARGE_V3,
            db=None,
        )


@pytest.mark.asyncio
async def test_create_transcription_wrong_user(transcription_service):
    """Test error when creating a transcription for another user's audio."""
    with pytest.raises(TranscriptionError):
        await transcription_service.create_transcription(
            audio_id="123e4567-e89b-12d3-a456-426614174000",
            user_id=2,  # Different user
            model=TranscriptionModel.WHISPER_LARGE_V3,
            db=None,
        )


@pytest.mark.asyncio
async def test_process_transcription(transcription_service):
    """Test processing a transcription."""
    transcription = await transcription_service.process_transcription(
        transcription_id="123e4567-e89b-12d3-a456-426614174001",
        db=None,
    )
    
    assert transcription is not None
    assert transcription.status == TranscriptionStatus.COMPLETED
    assert transcription.progress == 100
    
    transcription_service.transcription_repository.get_by_id.assert_called_once_with(
        "123e4567-e89b-12d3-a456-426614174001", db=None
    )
    transcription_service.audio_repository.get_by_id.assert_called_once_with(
        "123e4567-e89b-12d3-a456-426614174000", db=None
    )
    transcription_service.audio_processor.convert_to_wav.assert_called_once()
    transcription_service.audio_processor.normalize_volume.assert_called_once()
    transcription_service.whisper_service.transcribe.assert_called_once()
    transcription_service.transcription_segment_repository.create.assert_called()
    transcription_service.transcription_repository.update.assert_called()


@pytest.mark.asyncio
async def test_get_transcription(transcription_service):
    """Test getting a transcription."""
    transcription = await transcription_service.get_transcription(
        transcription_id="123e4567-e89b-12d3-a456-426614174001",
        include_segments=True,
        db=None,
    )
    
    assert transcription is not None
    assert transcription.id == "123e4567-e89b-12d3-a456-426614174001"
    assert len(transcription.segments) == 2
    
    transcription_service.transcription_repository.get_by_id.assert_called_once_with(
        "123e4567-e89b-12d3-a456-426614174001", db=None
    )
    transcription_service.transcription_segment_repository.get_by_transcription_id.assert_called_once_with(
        "123e4567-e89b-12d3-a456-426614174001", db=None
    )
```

#### Критерии для ручного тестирования

1. **Проверка загрузки моделей:**
   - Запустите сервис и убедитесь, что модели загружаются без ошибок
   - Проверьте, что модели кэшируются и не загружаются повторно
   - Убедитесь, что используется GPU, если доступно

2. **Проверка транскрипции:**
   - Транскрибируйте аудиофайлы различной длительности и качества
   - Проверьте точность транскрипции для русского и английского языков
   - Убедитесь, что временные метки соответствуют реальному времени в аудио

3. **Проверка определения языка:**
   - Проверьте автоматическое определение языка для русских и английских аудио
   - Убедитесь, что определение языка работает корректно для смешанных аудио
   - Проверьте, что можно указать язык вручную

4. **Проверка API:**
   - Создайте задачу транскрипции через API
   - Получите список задач и убедитесь, что новая задача присутствует
   - Получите результаты транскрипции и проверьте их корректность

5. **Проверка обработки ошибок:**
   - Попробуйте транскрибировать поврежденный аудиофайл
   - Проверьте, что ошибки обрабатываются корректно
   - Убедитесь, что пользователь получает понятные сообщения об ошибках

6. **Проверка производительности:**
   - Измерьте время транскрипции для файлов различной длительности
   - Сравните производительность моделей large-v3 и turbo
   - Проверьте использование памяти при транскрипции больших файлов

## Вопросы к постановщику задачи
1. Какие дополнительные языки нужно поддерживать помимо русского и английского?
2. Требуется ли поддержка многоязычной транскрипции в рамках одного файла?
3. Какие конкретные метрики качества транскрипции нужно отслеживать?
4. Требуется ли реализация дополнительных функций Whisper (например, перевод)?
5. Какие ограничения по ресурсам (CPU, RAM, GPU) существуют для транскрипции?