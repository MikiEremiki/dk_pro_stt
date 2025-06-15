# Фаза 2, День 3. Диаризация с pyannote.audio

## Цель (Definition of Done)
- Настроена интеграция с pyannote.audio 3.1 для диаризации спикеров
- Реализован сервис для разделения речи по спикерам
- Настроено автоматическое определение количества спикеров (до 10)
- Реализована обработка минимальных сегментов длительностью 0.5 секунды
- Настроена интеграция с сервисом транскрипции для объединения результатов
- Реализована оптимизация производительности и кэширование моделей
- Написаны тесты для проверки функциональности диаризации

## Ссылки на документацию
- [pyannote.audio Documentation](https://github.com/pyannote/pyannote-audio)
- [pyannote.core Documentation](https://github.com/pyannote/pyannote-core)
- [HuggingFace pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)
- [CUDA Documentation](https://docs.nvidia.com/cuda/index.html)

---

### 1. Техническая секция

#### Описание
В этом задании необходимо реализовать интеграцию с библиотекой pyannote.audio для диаризации спикеров в аудиофайлах. Диаризация - это процесс разделения аудиозаписи на сегменты в соответствии с тем, кто говорит в каждый момент времени. Мы будем использовать модель pyannote/speaker-diarization-3.1, которая обеспечивает высокую точность разделения спикеров.

Основные компоненты:
1. **Загрузка и кэширование модели** - эффективная загрузка модели pyannote.audio и её кэширование
2. **Диаризация аудио** - разделение аудио на сегменты по спикерам
3. **Определение количества спикеров** - автоматическое определение количества говорящих
4. **Оптимизация производительности** - настройка параметров для оптимальной работы модели
5. **Интеграция с транскрипцией** - объединение результатов диаризации и транскрипции

#### Примеры кода

**Сервис для диаризации с использованием pyannote.audio:**
```python
# src/domains/diarization/services/diarization_service.py
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import structlog
import torch
from pyannote.audio import Pipeline
from pyannote.core import Annotation, Segment

from src.config.settings import config
from src.domains.diarization.entities import DiarizationResult, SpeakerSegment
from src.domains.diarization.exceptions import DiarizationError

logger = structlog.get_logger()


class DiarizationService:
    """Service for speaker diarization using pyannote.audio."""

    def __init__(self):
        """Initialize the diarization service."""
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Create model cache directory if it doesn't exist
        os.makedirs(config.MODEL_CACHE_DIR, exist_ok=True)
        
        logger.info(
            "Initialized DiarizationService",
            device=self.device,
            model_cache_dir=str(config.MODEL_CACHE_DIR),
        )

    async def load_model(self) -> None:
        """Load the diarization model.

        Raises:
            DiarizationError: If there's an error loading the model.
        """
        try:
            if self.model is not None:
                return
            
            # Log model loading
            logger.info(
                "Loading pyannote.audio diarization model",
                device=self.device,
            )
            
            # Load model
            self.model = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=config.HUGGINGFACE_TOKEN,
                cache_dir=str(config.MODEL_CACHE_DIR),
            )
            
            # Move model to device
            self.model = self.model.to(self.device)
            
            # Log model loading completion
            logger.info(
                "pyannote.audio diarization model loaded",
                device=self.device,
            )
        except Exception as e:
            logger.error(
                "Error loading diarization model",
                error=str(e),
                exc_info=True,
            )
            raise DiarizationError(f"Error loading diarization model: {str(e)}")

    async def diarize(
        self,
        audio_path: Path,
        min_speakers: int = 1,
        max_speakers: int = 10,
        min_segment_duration: float = 0.5,
    ) -> DiarizationResult:
        """Perform speaker diarization on an audio file.

        Args:
            audio_path: Path to the audio file.
            min_speakers: Minimum number of speakers to detect.
            max_speakers: Maximum number of speakers to detect.
            min_segment_duration: Minimum duration of a speaker segment in seconds.

        Returns:
            DiarizationResult containing speaker segments.

        Raises:
            DiarizationError: If there's an error during diarization.
        """
        try:
            # Load model if not already loaded
            await self.load_model()
            
            # Log diarization start
            logger.info(
                "Starting diarization",
                audio_path=str(audio_path),
                min_speakers=min_speakers,
                max_speakers=max_speakers,
                min_segment_duration=min_segment_duration,
            )
            
            # Perform diarization
            diarization = self.model(
                str(audio_path),
                min_speakers=min_speakers,
                max_speakers=max_speakers,
            )
            
            # Process diarization result
            speaker_segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                # Skip segments shorter than min_segment_duration
                if turn.duration < min_segment_duration:
                    continue
                
                # Create SpeakerSegment
                segment = SpeakerSegment(
                    start_time=turn.start,
                    end_time=turn.end,
                    speaker_id=speaker,
                )
                speaker_segments.append(segment)
            
            # Sort segments by start time
            speaker_segments.sort(key=lambda x: x.start_time)
            
            # Count unique speakers
            unique_speakers = len(set(segment.speaker_id for segment in speaker_segments))
            
            # Create DiarizationResult
            result = DiarizationResult(
                segments=speaker_segments,
                num_speakers=unique_speakers,
            )
            
            # Log diarization completion
            logger.info(
                "Diarization completed",
                audio_path=str(audio_path),
                num_speakers=unique_speakers,
                num_segments=len(speaker_segments),
            )
            
            return result
        except Exception as e:
            logger.error(
                "Error during diarization",
                audio_path=str(audio_path),
                error=str(e),
                exc_info=True,
            )
            raise DiarizationError(f"Error during diarization: {str(e)}")

    async def merge_with_transcription(
        self,
        diarization_result: DiarizationResult,
        transcription_segments: List[dict],
        overlap_threshold: float = 0.5,
    ) -> List[dict]:
        """Merge diarization result with transcription segments.

        Args:
            diarization_result: Result of diarization.
            transcription_segments: List of transcription segments with start_time, end_time, and text.
            overlap_threshold: Minimum overlap ratio to assign a speaker to a transcription segment.

        Returns:
            List of transcription segments with speaker_id added.
        """
        try:
            # Log merge start
            logger.info(
                "Merging diarization with transcription",
                num_diarization_segments=len(diarization_result.segments),
                num_transcription_segments=len(transcription_segments),
            )
            
            # Create a copy of transcription segments to avoid modifying the original
            merged_segments = []
            
            for trans_segment in transcription_segments:
                trans_start = trans_segment["start_time"]
                trans_end = trans_segment["end_time"]
                trans_duration = trans_end - trans_start
                
                # Find overlapping diarization segments
                overlapping_speakers = {}
                
                for diar_segment in diarization_result.segments:
                    # Calculate overlap
                    overlap_start = max(trans_start, diar_segment.start_time)
                    overlap_end = min(trans_end, diar_segment.end_time)
                    
                    if overlap_start < overlap_end:
                        overlap_duration = overlap_end - overlap_start
                        overlap_ratio = overlap_duration / trans_duration
                        
                        # Add speaker to overlapping speakers with overlap ratio
                        if diar_segment.speaker_id in overlapping_speakers:
                            overlapping_speakers[diar_segment.speaker_id] += overlap_ratio
                        else:
                            overlapping_speakers[diar_segment.speaker_id] = overlap_ratio
                
                # Assign speaker with highest overlap ratio if above threshold
                speaker_id = None
                max_overlap = 0
                
                for speaker, overlap in overlapping_speakers.items():
                    if overlap > max_overlap and overlap >= overlap_threshold:
                        max_overlap = overlap
                        speaker_id = speaker
                
                # Create merged segment
                merged_segment = dict(trans_segment)
                merged_segment["speaker_id"] = speaker_id
                merged_segments.append(merged_segment)
            
            # Log merge completion
            logger.info(
                "Merge completed",
                num_merged_segments=len(merged_segments),
            )
            
            return merged_segments
        except Exception as e:
            logger.error(
                "Error merging diarization with transcription",
                error=str(e),
                exc_info=True,
            )
            raise DiarizationError(f"Error merging diarization with transcription: {str(e)}")
```

**Сущности для диаризации:**
```python
# src/domains/diarization/entities.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID


@dataclass
class SpeakerSegment:
    """Entity representing a speaker segment."""
    start_time: float
    end_time: float
    speaker_id: str
    id: Optional[str] = None
    diarization_id: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class DiarizationResult:
    """Entity representing a diarization result."""
    segments: List[SpeakerSegment]
    num_speakers: int
    id: Optional[str] = None
    audio_id: Optional[str] = None
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None
```

**Исключения для диаризации:**
```python
# src/domains/diarization/exceptions.py
class DiarizationError(Exception):
    """Base exception for diarization errors."""
    pass


class ModelLoadingError(DiarizationError):
    """Exception raised when there's an error loading a model."""
    pass


class UnsupportedAudioError(DiarizationError):
    """Exception raised when the audio format is not supported."""
    pass
```

**Интеграция с сервисом транскрипции:**
```python
# src/domains/transcription/services/combined_service.py
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.audio.entities import AudioFile
from src.domains.audio.repositories import AudioRepository
from src.domains.audio.services.audio_processor import AudioProcessor
from src.domains.diarization.entities import DiarizationResult
from src.domains.diarization.services.diarization_service import DiarizationService
from src.domains.transcription.entities import (
    CombinedResult,
    Transcription,
    TranscriptionModel,
    TranscriptionSegment,
    TranscriptionStatus,
)
from src.domains.transcription.exceptions import TranscriptionError
from src.domains.transcription.repositories import TranscriptionRepository, TranscriptionSegmentRepository
from src.domains.transcription.services.whisper_service import WhisperService

logger = structlog.get_logger()


class CombinedService:
    """Service for combining transcription and diarization."""

    def __init__(
        self,
        transcription_repository: TranscriptionRepository,
        transcription_segment_repository: TranscriptionSegmentRepository,
        audio_repository: AudioRepository,
        audio_processor: AudioProcessor,
        whisper_service: WhisperService,
        diarization_service: DiarizationService,
    ):
        """Initialize the combined service.

        Args:
            transcription_repository: Repository for transcriptions.
            transcription_segment_repository: Repository for transcription segments.
            audio_repository: Repository for audio files.
            audio_processor: Service for processing audio files.
            whisper_service: Service for transcribing audio.
            diarization_service: Service for speaker diarization.
        """
        self.transcription_repository = transcription_repository
        self.transcription_segment_repository = transcription_segment_repository
        self.audio_repository = audio_repository
        self.audio_processor = audio_processor
        self.whisper_service = whisper_service
        self.diarization_service = diarization_service
        self.logger = structlog.get_logger()

    async def process_audio(
        self,
        audio_id: str,
        user_id: int,
        model: TranscriptionModel = TranscriptionModel.WHISPER_LARGE_V3,
        language: Optional[str] = None,
        min_speakers: int = 1,
        max_speakers: int = 10,
        min_segment_duration: float = 0.5,
        db: AsyncSession = None,
    ) -> CombinedResult:
        """Process audio with transcription and diarization.

        Args:
            audio_id: ID of the audio file to process.
            user_id: ID of the user who created the task.
            model: Transcription model to use.
            language: Language code (e.g., "en", "ru"). If None, language will be auto-detected.
            min_speakers: Minimum number of speakers to detect.
            max_speakers: Maximum number of speakers to detect.
            min_segment_duration: Minimum duration of a speaker segment in seconds.
            db: Database session.

        Returns:
            CombinedResult containing transcription and diarization.

        Raises:
            TranscriptionError: If there's an error during processing.
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
            
            # Update status to in progress
            transcription.status = TranscriptionStatus.IN_PROGRESS
            transcription.progress = 10
            transcription = await self.transcription_repository.update(transcription, db=db)
            
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
            
            # Perform diarization
            diarization_result = await self.diarization_service.diarize(
                normalized_path,
                min_speakers=min_speakers,
                max_speakers=max_speakers,
                min_segment_duration=min_segment_duration,
            )
            transcription.progress = 60
            transcription = await self.transcription_repository.update(transcription, db=db)
            
            # Transcribe audio
            transcription_segments, detected_language = await self.whisper_service.transcribe(
                normalized_path,
                model_name=transcription.model,
                language=transcription.language,
            )
            
            # Update language if it was auto-detected
            if not transcription.language:
                transcription.language = detected_language
            
            # Merge diarization and transcription
            transcription_segments_dict = [
                {
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "text": segment.text,
                    "confidence": segment.confidence,
                }
                for segment in transcription_segments
            ]
            
            merged_segments = await self.diarization_service.merge_with_transcription(
                diarization_result,
                transcription_segments_dict,
            )
            
            # Save segments to database
            for segment_dict in merged_segments:
                segment = TranscriptionSegment(
                    transcription_id=transcription_id,
                    start_time=segment_dict["start_time"],
                    end_time=segment_dict["end_time"],
                    text=segment_dict["text"],
                    confidence=segment_dict["confidence"],
                    speaker_id=segment_dict["speaker_id"],
                )
                await self.transcription_segment_repository.create(segment, db=db)
            
            # Update transcription status
            transcription.status = TranscriptionStatus.COMPLETED
            transcription.progress = 100
            transcription = await self.transcription_repository.update(transcription, db=db)
            
            # Create combined result
            combined_result = CombinedResult(
                transcription=transcription,
                segments=merged_segments,
                num_speakers=diarization_result.num_speakers,
            )
            
            # Log completion
            self.logger.info(
                "Combined processing completed",
                transcription_id=transcription_id,
                audio_id=audio_id,
                user_id=user_id,
                model=model,
                language=transcription.language,
                num_speakers=diarization_result.num_speakers,
                num_segments=len(merged_segments),
            )
            
            return combined_result
        except Exception as e:
            # Update transcription status to failed
            if transcription:
                transcription.status = TranscriptionStatus.FAILED
                transcription.error_message = str(e)
                await self.transcription_repository.update(transcription, db=db)
            
            self.logger.error(
                "Error during combined processing",
                audio_id=audio_id,
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            raise TranscriptionError(f"Error during combined processing: {str(e)}")
```

**Обновление сущностей для транскрипции:**
```python
# src/domains/transcription/entities.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
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
    speaker_id: Optional[str] = None
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


@dataclass
class CombinedResult:
    """Entity representing a combined transcription and diarization result."""
    transcription: Transcription
    segments: List[Dict]
    num_speakers: int
```

**Интеграция с FastAPI для диаризации:**
```python
# src/application/api/routes/diarization.py
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.api.dependencies import get_current_user, get_db
from src.domains.diarization.exceptions import DiarizationError
from src.domains.diarization.schemas import DiarizationRequest, DiarizationResponse
from src.domains.diarization.services.diarization_service import DiarizationService
from src.domains.transcription.entities import TranscriptionModel
from src.domains.transcription.schemas import CombinedResultResponse
from src.domains.transcription.services.combined_service import CombinedService
from src.domains.user.schemas import UserResponse

router = APIRouter()


@router.post("/process", response_model=CombinedResultResponse)
async def process_audio(
    request: DiarizationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    combined_service: CombinedService = Depends(),
):
    """Process audio with transcription and diarization."""
    try:
        result = await combined_service.process_audio(
            audio_id=str(request.audio_id),
            user_id=current_user.id,
            model=request.model,
            language=request.language,
            min_speakers=request.min_speakers,
            max_speakers=request.max_speakers,
            min_segment_duration=request.min_segment_duration,
            db=db,
        )
        
        return result
    except DiarizationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing audio: {str(e)}",
        )
```

#### Схемы данных/API

**Структура диаризации:**
```
1. Пользователь создает задачу обработки аудио с транскрипцией и диаризацией
2. Система проверяет, что аудиофайл существует и принадлежит пользователю
3. Система создает запись о транскрипции в базе данных со статусом "pending"
4. Система конвертирует аудиофайл в WAV, если необходимо
5. Система нормализует громкость аудио
6. Система определяет язык аудио, если не указан
7. Система выполняет диаризацию с использованием pyannote.audio
8. Система выполняет транскрипцию с использованием выбранной модели Whisper
9. Система объединяет результаты диаризации и транскрипции
10. Система сохраняет сегменты в базе данных
11. Система обновляет статус транскрипции на "completed"
12. Пользователь может получить результаты через API
```

**Диаграмма последовательности диаризации:**
```
User -> API: Process audio request
API -> CombinedService: process_audio()
CombinedService -> AudioRepository: Get audio file
AudioRepository -> CombinedService: Audio file
CombinedService -> TranscriptionRepository: Create transcription
TranscriptionRepository -> CombinedService: Transcription entity

CombinedService -> AudioProcessor: convert_to_wav() if needed
AudioProcessor -> CombinedService: WAV file path
CombinedService -> AudioProcessor: normalize_volume()
AudioProcessor -> CombinedService: Normalized file path

alt language not specified
    CombinedService -> WhisperService: detect_language()
    WhisperService -> CombinedService: Detected language
    CombinedService -> TranscriptionRepository: Update language
end

CombinedService -> DiarizationService: diarize()
DiarizationService -> CombinedService: Diarization result

CombinedService -> WhisperService: transcribe()
WhisperService -> CombinedService: Transcription segments

CombinedService -> DiarizationService: merge_with_transcription()
DiarizationService -> CombinedService: Merged segments

CombinedService -> TranscriptionSegmentRepository: Save segments
CombinedService -> TranscriptionRepository: Update status to "completed"
CombinedService -> API: Combined result
API -> User: Combined result response
```

### 2. Практическая секция

#### Пошаговые инструкции

1. **Настройка зависимостей:**
   - Установите необходимые пакеты: pyannote.audio, pyannote.core, torch
   - Получите токен доступа к HuggingFace для загрузки модели
   - Настройте CUDA, если доступно, для ускорения обработки

2. **Реализация сервиса диаризации:**
   - Создайте класс DiarizationService для работы с pyannote.audio
   - Реализуйте загрузку и кэширование модели
   - Добавьте метод для диаризации аудио
   - Реализуйте метод для объединения результатов диаризации и транскрипции

3. **Реализация сущностей и исключений:**
   - Создайте сущности для представления результатов диаризации
   - Реализуйте исключения для обработки ошибок
   - Обновите сущности транскрипции для поддержки информации о спикерах

4. **Реализация комбинированного сервиса:**
   - Создайте класс CombinedService для объединения транскрипции и диаризации
   - Реализуйте метод для обработки аудио с транскрипцией и диаризацией
   - Добавьте логику для объединения результатов

5. **Реализация API эндпоинтов:**
   - Создайте роутер для работы с диаризацией
   - Реализуйте эндпоинт для обработки аудио с транскрипцией и диаризацией
   - Добавьте валидацию и обработку ошибок

6. **Оптимизация производительности:**
   - Настройте параметры модели для оптимальной производительности
   - Реализуйте кэширование модели для ускорения загрузки
   - Добавьте асинхронную обработку для длительных операций

7. **Написание тестов:**
   - Создайте тесты для сервиса диаризации
   - Добавьте тесты для комбинированного сервиса
   - Реализуйте тесты для API эндпоинтов

#### Частые ошибки (Common Pitfalls)

1. **Проблемы с моделью pyannote.audio:**
   - Отсутствие токена доступа к HuggingFace
   - Неправильные пути к модели
   - Недостаточно памяти для загрузки модели

2. **Проблемы с CUDA:**
   - Несовместимость версий CUDA и PyTorch
   - Недостаточно видеопамяти для модели
   - Неправильная настройка CUDA для использования GPU

3. **Проблемы с обработкой аудио:**
   - Неподдерживаемые форматы аудио
   - Слишком большие файлы, вызывающие проблемы с памятью
   - Низкое качество аудио, влияющее на точность диаризации

4. **Проблемы с объединением результатов:**
   - Неправильное сопоставление сегментов транскрипции и диаризации
   - Потеря информации о спикерах при объединении
   - Неправильная обработка перекрывающихся сегментов

#### Советы по оптимизации (Performance Tips)

1. **Оптимизация модели pyannote.audio:**
   - Используйте CUDA для ускорения обработки на GPU
   - Настройте параметры модели для оптимального баланса между точностью и скоростью
   - Используйте кэширование модели для ускорения загрузки

2. **Оптимизация обработки аудио:**
   - Предварительно обрабатывайте аудио для улучшения качества диаризации
   - Используйте нормализацию громкости для более точного определения спикеров
   - Разбивайте большие файлы на сегменты для параллельной обработки

3. **Оптимизация объединения результатов:**
   - Используйте эффективные алгоритмы для сопоставления сегментов
   - Настройте параметры объединения для оптимального баланса между точностью и скоростью
   - Кэшируйте промежуточные результаты для ускорения обработки

### 3. Валидационная секция

#### Чек-лист для самопроверки

- [ ] Модель pyannote.audio успешно интегрирована
- [ ] Реализован сервис для диаризации спикеров
- [ ] Настроено автоматическое определение количества спикеров
- [ ] Реализована обработка минимальных сегментов
- [ ] Настроена интеграция с сервисом транскрипции
- [ ] Реализована оптимизация производительности
- [ ] Настроено кэширование модели
- [ ] Написаны тесты для проверки функциональности
- [ ] Обработка ошибок реализована и тестируется
- [ ] Код соответствует PEP 8 и включает типизацию
- [ ] Документация к коду добавлена и актуальна

#### Автоматизированные тесты

```python
# tests/domains/diarization/services/test_diarization_service.py
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import torch

from src.domains.diarization.entities import DiarizationResult, SpeakerSegment
from src.domains.diarization.exceptions import DiarizationError
from src.domains.diarization.services.diarization_service import DiarizationService


@pytest.fixture
def diarization_service():
    """Create a DiarizationService instance."""
    with patch("src.domains.diarization.services.diarization_service.Pipeline") as mock_pipeline:
        # Mock the Pipeline to avoid actual model loading
        mock_pipeline.from_pretrained.return_value = MagicMock()
        
        # Mock the diarization result
        mock_diarization = MagicMock()
        mock_diarization.itertracks.return_value = [
            (MagicMock(start=0.0, end=2.0, duration=2.0), None, "speaker_0"),
            (MagicMock(start=2.0, end=4.0, duration=2.0), None, "speaker_1"),
            (MagicMock(start=4.0, end=6.0, duration=2.0), None, "speaker_0"),
        ]
        
        mock_pipeline.from_pretrained.return_value.return_value = mock_diarization
        
        service = DiarizationService()
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
async def test_load_model(diarization_service):
    """Test loading the diarization model."""
    await diarization_service.load_model()
    
    assert diarization_service.model is not None


@pytest.mark.asyncio
async def test_diarize(diarization_service, sample_audio_file):
    """Test diarizing audio."""
    result = await diarization_service.diarize(
        audio_path=sample_audio_file,
        min_speakers=1,
        max_speakers=10,
        min_segment_duration=0.5,
    )
    
    assert isinstance(result, DiarizationResult)
    assert result.num_speakers == 2
    assert len(result.segments) == 3
    
    assert result.segments[0].start_time == 0.0
    assert result.segments[0].end_time == 2.0
    assert result.segments[0].speaker_id == "speaker_0"
    
    assert result.segments[1].start_time == 2.0
    assert result.segments[1].end_time == 4.0
    assert result.segments[1].speaker_id == "speaker_1"
    
    assert result.segments[2].start_time == 4.0
    assert result.segments[2].end_time == 6.0
    assert result.segments[2].speaker_id == "speaker_0"


@pytest.mark.asyncio
async def test_merge_with_transcription(diarization_service):
    """Test merging diarization with transcription."""
    # Create diarization result
    diarization_result = DiarizationResult(
        segments=[
            SpeakerSegment(start_time=0.0, end_time=2.0, speaker_id="speaker_0"),
            SpeakerSegment(start_time=2.0, end_time=4.0, speaker_id="speaker_1"),
            SpeakerSegment(start_time=4.0, end_time=6.0, speaker_id="speaker_0"),
        ],
        num_speakers=2,
    )
    
    # Create transcription segments
    transcription_segments = [
        {
            "start_time": 0.5,
            "end_time": 2.5,
            "text": "Hello, world!",
            "confidence": 0.9,
        },
        {
            "start_time": 2.5,
            "end_time": 4.5,
            "text": "This is a test.",
            "confidence": 0.8,
        },
    ]
    
    # Merge
    merged_segments = await diarization_service.merge_with_transcription(
        diarization_result,
        transcription_segments,
    )
    
    assert len(merged_segments) == 2
    
    assert merged_segments[0]["start_time"] == 0.5
    assert merged_segments[0]["end_time"] == 2.5
    assert merged_segments[0]["text"] == "Hello, world!"
    assert merged_segments[0]["confidence"] == 0.9
    assert merged_segments[0]["speaker_id"] == "speaker_0"
    
    assert merged_segments[1]["start_time"] == 2.5
    assert merged_segments[1]["end_time"] == 4.5
    assert merged_segments[1]["text"] == "This is a test."
    assert merged_segments[1]["confidence"] == 0.8
    assert merged_segments[1]["speaker_id"] == "speaker_1"


# tests/domains/transcription/services/test_combined_service.py
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domains.audio.entities import AudioFile, AudioFormat
from src.domains.diarization.entities import DiarizationResult, SpeakerSegment
from src.domains.transcription.entities import (
    CombinedResult,
    Transcription,
    TranscriptionModel,
    TranscriptionSegment,
    TranscriptionStatus,
)
from src.domains.transcription.exceptions import TranscriptionError
from src.domains.transcription.services.combined_service import CombinedService


@pytest.fixture
def combined_service():
    """Create a CombinedService instance with mocked dependencies."""
    transcription_repository = AsyncMock()
    transcription_segment_repository = AsyncMock()
    audio_repository = AsyncMock()
    audio_processor = AsyncMock()
    whisper_service = AsyncMock()
    diarization_service = AsyncMock()
    
    service = CombinedService(
        transcription_repository=transcription_repository,
        transcription_segment_repository=transcription_segment_repository,
        audio_repository=audio_repository,
        audio_processor=audio_processor,
        whisper_service=whisper_service,
        diarization_service=diarization_service,
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
    
    transcription_segments = [
        TranscriptionSegment(
            start_time=0.0,
            end_time=2.0,
            text="Hello, world!",
            confidence=0.9,
        ),
        TranscriptionSegment(
            start_time=2.0,
            end_time=4.0,
            text="This is a test.",
            confidence=0.8,
        ),
    ]
    
    diarization_result = DiarizationResult(
        segments=[
            SpeakerSegment(start_time=0.0, end_time=2.0, speaker_id="speaker_0"),
            SpeakerSegment(start_time=2.0, end_time=4.0, speaker_id="speaker_1"),
        ],
        num_speakers=2,
    )
    
    merged_segments = [
        {
            "start_time": 0.0,
            "end_time": 2.0,
            "text": "Hello, world!",
            "confidence": 0.9,
            "speaker_id": "speaker_0",
        },
        {
            "start_time": 2.0,
            "end_time": 4.0,
            "text": "This is a test.",
            "confidence": 0.8,
            "speaker_id": "speaker_1",
        },
    ]
    
    audio_repository.get_by_id.return_value = audio_file
    transcription_repository.create.return_value = transcription
    transcription_repository.update.return_value = transcription
    
    audio_processor.convert_to_wav.return_value = Path("/tmp/test.wav")
    audio_processor.normalize_volume.return_value = Path("/tmp/test_normalized.wav")
    
    whisper_service.detect_language.return_value = "en"
    whisper_service.transcribe.return_value = (transcription_segments, "en")
    
    diarization_service.diarize.return_value = diarization_result
    diarization_service.merge_with_transcription.return_value = merged_segments
    
    # Add service to the fixture
    service.audio_repository = audio_repository
    service.transcription_repository = transcription_repository
    service.transcription_segment_repository = transcription_segment_repository
    service.audio_processor = audio_processor
    service.whisper_service = whisper_service
    service.diarization_service = diarization_service
    
    return service


@pytest.mark.asyncio
async def test_process_audio(combined_service):
    """Test processing audio with transcription and diarization."""
    result = await combined_service.process_audio(
        audio_id="123e4567-e89b-12d3-a456-426614174000",
        user_id=1,
        model=TranscriptionModel.WHISPER_LARGE_V3,
        db=None,
    )
    
    assert isinstance(result, CombinedResult)
    assert result.transcription.id == "123e4567-e89b-12d3-a456-426614174001"
    assert result.transcription.audio_id == "123e4567-e89b-12d3-a456-426614174000"
    assert result.transcription.user_id == 1
    assert result.transcription.model == TranscriptionModel.WHISPER_LARGE_V3
    assert result.transcription.status == TranscriptionStatus.COMPLETED
    assert result.num_speakers == 2
    assert len(result.segments) == 2
    
    combined_service.audio_repository.get_by_id.assert_called_once_with(
        "123e4567-e89b-12d3-a456-426614174000", db=None
    )
    combined_service.transcription_repository.create.assert_called_once()
    combined_service.audio_processor.convert_to_wav.assert_called_once()
    combined_service.audio_processor.normalize_volume.assert_called_once()
    combined_service.whisper_service.transcribe.assert_called_once()
    combined_service.diarization_service.diarize.assert_called_once()
    combined_service.diarization_service.merge_with_transcription.assert_called_once()
    combined_service.transcription_segment_repository.create.assert_called()
    combined_service.transcription_repository.update.assert_called()


@pytest.mark.asyncio
async def test_process_audio_audio_not_found(combined_service):
    """Test error when processing audio with non-existent audio."""
    combined_service.audio_repository.get_by_id.return_value = None
    
    with pytest.raises(TranscriptionError):
        await combined_service.process_audio(
            audio_id="non-existent",
            user_id=1,
            model=TranscriptionModel.WHISPER_LARGE_V3,
            db=None,
        )


@pytest.mark.asyncio
async def test_process_audio_wrong_user(combined_service):
    """Test error when processing audio for another user's audio."""
    with pytest.raises(TranscriptionError):
        await combined_service.process_audio(
            audio_id="123e4567-e89b-12d3-a456-426614174000",
            user_id=2,  # Different user
            model=TranscriptionModel.WHISPER_LARGE_V3,
            db=None,
        )
```

#### Критерии для ручного тестирования

1. **Проверка загрузки модели:**
   - Запустите сервис и убедитесь, что модель pyannote.audio загружается без ошибок
   - Проверьте, что модель кэшируется и не загружается повторно
   - Убедитесь, что используется GPU, если доступно

2. **Проверка диаризации:**
   - Диаризируйте аудиофайлы с разным количеством спикеров
   - Проверьте точность определения количества спикеров
   - Убедитесь, что минимальные сегменты обрабатываются корректно

3. **Проверка объединения результатов:**
   - Обработайте аудио с транскрипцией и диаризацией
   - Проверьте, что спикеры правильно сопоставлены с сегментами транскрипции
   - Убедитесь, что перекрывающиеся сегменты обрабатываются корректно

4. **Проверка API:**
   - Создайте задачу обработки аудио через API
   - Получите результаты и убедитесь, что они содержат информацию о спикерах
   - Проверьте, что результаты соответствуют ожиданиям

5. **Проверка обработки ошибок:**
   - Попробуйте диаризировать поврежденный аудиофайл
   - Проверьте, что ошибки обрабатываются корректно
   - Убедитесь, что пользователь получает понятные сообщения об ошибках

6. **Проверка производительности:**
   - Измерьте время диаризации для файлов различной длительности
   - Проверьте использование памяти при диаризации больших файлов
   - Сравните производительность с использованием GPU и без него

## Вопросы к постановщику задачи
1. Какие дополнительные параметры диаризации нужно настроить для оптимальной работы?
2. Требуется ли поддержка определения пола спикеров?
3. Какие конкретные метрики качества диаризации нужно отслеживать?
4. Требуется ли реализация дополнительных функций pyannote.audio (например, сегментация речи/музыки)?
5. Какие ограничения по ресурсам (CPU, RAM, GPU) существуют для диаризации?