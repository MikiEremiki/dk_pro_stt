# Фаза 2, День 1. Обработка аудио

## Цель (Definition of Done)
- Реализована интеграция с FFmpeg для обработки аудиофайлов
- Настроена валидация форматов аудиофайлов (mp3, wav, ogg, m4a, webm)
- Реализована конвертация аудиофайлов в формат, подходящий для транскрипции
- Реализована нормализация громкости аудио
- Реализовано определение длительности аудиофайлов
- Реализовано детектирование тишины для оптимизации обработки
- Написаны тесты для проверки функциональности обработки аудио

## Ссылки на документацию
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [ffmpeg-python Documentation](https://github.com/kkroening/ffmpeg-python)
- [librosa Documentation](https://librosa.org/doc/latest/index.html)
- [pydub Documentation](https://github.com/jiaaro/pydub)
- [pytest Documentation](https://docs.pytest.org/en/latest/)

---

### 1. Техническая секция

#### Описание
В этом задании необходимо реализовать функциональность для обработки аудиофайлов, которая будет использоваться в сервисе транскрипции. Обработка аудио включает в себя валидацию форматов, конвертацию, нормализацию громкости и другие операции, необходимые для подготовки аудиофайлов к транскрипции и диаризации.

Основные компоненты:
1. **Валидация аудиофайлов** - проверка формата и размера файлов
2. **Конвертация форматов** - преобразование различных форматов в WAV для обработки
3. **Нормализация громкости** - выравнивание уровня громкости для улучшения качества транскрипции
4. **Определение длительности** - получение длительности аудиофайлов
5. **Детектирование тишины** - определение участков тишины для оптимизации обработки

#### Примеры кода

**Сервис для обработки аудио:**
```python
# src/domains/audio/services/audio_processor.py
import os
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple, BinaryIO
from uuid import UUID, uuid4

import ffmpeg
import librosa
import numpy as np
import structlog
from fastapi import UploadFile
from pydub import AudioSegment

from src.config.settings import config
from src.domains.audio.entities import AudioFile, AudioFormat
from src.domains.audio.exceptions import AudioProcessingError, InvalidAudioFormatError

logger = structlog.get_logger()


class AudioProcessor:
    """Service for processing audio files."""

    SUPPORTED_FORMATS = {
        "mp3": AudioFormat.MP3,
        "wav": AudioFormat.WAV,
        "ogg": AudioFormat.OGG,
        "m4a": AudioFormat.M4A,
        "webm": AudioFormat.WEBM,
    }

    MAX_FILE_SIZE_BYTES = 200 * 1024 * 1024  # 200 MB

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize the audio processor.

        Args:
            storage_path: Path to store processed audio files.
                If not provided, uses the path from config.
        """
        self.storage_path = storage_path or config.STORAGE_PATH
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def validate_audio_file(self, file: BinaryIO, filename: str) -> Tuple[bool, Optional[str]]:
        """Validate audio file format and size.

        Args:
            file: File-like object.
            filename: Original filename.

        Returns:
            Tuple of (is_valid, error_message).
        """
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > self.MAX_FILE_SIZE_BYTES:
            return False, f"File size exceeds maximum allowed size of {self.MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB"

        # Check file format
        file_ext = self._get_file_extension(filename)
        if not file_ext or file_ext not in self.SUPPORTED_FORMATS:
            return False, f"Unsupported file format. Supported formats: {', '.join(self.SUPPORTED_FORMATS.keys())}"

        # Try to read file with ffmpeg to verify it's a valid audio file
        with tempfile.NamedTemporaryFile(suffix=f".{file_ext}") as temp_file:
            # Copy file content to temporary file
            temp_file.write(file.read())
            temp_file.flush()
            file.seek(0)

            try:
                # Try to get file info with ffmpeg
                probe = ffmpeg.probe(temp_file.name)
                if not probe or "streams" not in probe:
                    return False, "Invalid audio file: no audio streams found"

                # Check if there's at least one audio stream
                audio_streams = [s for s in probe["streams"] if s["codec_type"] == "audio"]
                if not audio_streams:
                    return False, "Invalid audio file: no audio streams found"

                return True, None
            except ffmpeg.Error as e:
                logger.error("FFmpeg error during audio validation", error=str(e))
                return False, f"Invalid audio file: {str(e)}"
            except Exception as e:
                logger.error("Error during audio validation", error=str(e))
                return False, f"Error validating audio file: {str(e)}"

    async def save_audio_file(self, file: BinaryIO, filename: str, user_id: int) -> AudioFile:
        """Save audio file and create AudioFile entity.

        Args:
            file: File-like object.
            filename: Original filename.
            user_id: ID of the user who uploaded the file.

        Returns:
            AudioFile entity.

        Raises:
            InvalidAudioFormatError: If the file format is not supported.
            AudioProcessingError: If there's an error processing the audio file.
        """
        # Validate file
        is_valid, error_message = await self.validate_audio_file(file, filename)
        if not is_valid:
            raise InvalidAudioFormatError(error_message or "Invalid audio file")

        # Get file extension and format
        file_ext = self._get_file_extension(filename)
        audio_format = self.SUPPORTED_FORMATS[file_ext]

        # Generate unique ID and path
        file_id = str(uuid4())
        file_path = self.storage_path / f"{file_id}.{file_ext}"

        # Save file
        try:
            with open(file_path, "wb") as f:
                f.write(file.read())
            file.seek(0)

            # Get file size
            file_size = file_path.stat().st_size

            # Get duration
            duration = await self.get_audio_duration(file_path)

            # Create AudioFile entity
            audio_file = AudioFile(
                id=file_id,
                user_id=user_id,
                original_filename=filename,
                format=audio_format,
                size_bytes=file_size,
                duration_seconds=duration,
                path=file_path,
                is_valid=True,
            )

            return audio_file
        except Exception as e:
            # Clean up file if there was an error
            if file_path.exists():
                file_path.unlink()
            logger.error("Error saving audio file", error=str(e))
            raise AudioProcessingError(f"Error saving audio file: {str(e)}")

    async def convert_to_wav(self, file_path: Path, target_path: Optional[Path] = None) -> Path:
        """Convert audio file to WAV format.

        Args:
            file_path: Path to the audio file.
            target_path: Path to save the converted file. If not provided,
                a path will be generated based on the original file path.

        Returns:
            Path to the converted WAV file.

        Raises:
            AudioProcessingError: If there's an error converting the file.
        """
        if not target_path:
            target_path = file_path.with_suffix(".wav")

        try:
            # Convert to WAV using ffmpeg
            (
                ffmpeg
                .input(str(file_path))
                .output(
                    str(target_path),
                    acodec="pcm_s16le",  # 16-bit PCM
                    ar=16000,  # 16kHz sample rate
                    ac=1,  # Mono
                )
                .overwrite_output()
                .run(quiet=True, capture_stdout=True, capture_stderr=True)
            )

            return target_path
        except ffmpeg.Error as e:
            logger.error("FFmpeg error during conversion to WAV", error=str(e))
            raise AudioProcessingError(f"Error converting audio to WAV: {str(e)}")
        except Exception as e:
            logger.error("Error during conversion to WAV", error=str(e))
            raise AudioProcessingError(f"Error converting audio to WAV: {str(e)}")

    async def normalize_volume(self, file_path: Path, target_path: Optional[Path] = None) -> Path:
        """Normalize audio volume.

        Args:
            file_path: Path to the audio file.
            target_path: Path to save the normalized file. If not provided,
                the original file will be overwritten.

        Returns:
            Path to the normalized audio file.

        Raises:
            AudioProcessingError: If there's an error normalizing the file.
        """
        if not target_path:
            target_path = file_path

        try:
            # Normalize volume using ffmpeg
            (
                ffmpeg
                .input(str(file_path))
                .filter("loudnorm", i=-23, lra=7, tp=-2)
                .output(str(target_path))
                .overwrite_output()
                .run(quiet=True, capture_stdout=True, capture_stderr=True)
            )

            return target_path
        except ffmpeg.Error as e:
            logger.error("FFmpeg error during volume normalization", error=str(e))
            raise AudioProcessingError(f"Error normalizing audio volume: {str(e)}")
        except Exception as e:
            logger.error("Error during volume normalization", error=str(e))
            raise AudioProcessingError(f"Error normalizing audio volume: {str(e)}")

    async def get_audio_duration(self, file_path: Path) -> float:
        """Get audio duration in seconds.

        Args:
            file_path: Path to the audio file.

        Returns:
            Duration in seconds.

        Raises:
            AudioProcessingError: If there's an error getting the duration.
        """
        try:
            # Get duration using ffmpeg
            probe = ffmpeg.probe(str(file_path))
            duration = float(probe["format"]["duration"])
            return duration
        except ffmpeg.Error as e:
            logger.error("FFmpeg error getting audio duration", error=str(e))
            raise AudioProcessingError(f"Error getting audio duration: {str(e)}")
        except Exception as e:
            logger.error("Error getting audio duration", error=str(e))
            raise AudioProcessingError(f"Error getting audio duration: {str(e)}")

    async def detect_silence(self, file_path: Path, silence_threshold_db: float = -50.0, min_silence_duration: float = 1.0) -> List[Tuple[float, float]]:
        """Detect silence periods in audio file.

        Args:
            file_path: Path to the audio file.
            silence_threshold_db: Threshold in dB below which audio is considered silence.
            min_silence_duration: Minimum duration of silence in seconds.

        Returns:
            List of (start_time, end_time) tuples representing silence periods.

        Raises:
            AudioProcessingError: If there's an error detecting silence.
        """
        try:
            # Load audio file
            y, sr = librosa.load(str(file_path), sr=None)

            # Convert to dB
            db = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
            
            # Calculate mean dB for each frame
            mean_db = np.mean(db, axis=0)
            
            # Find silence frames
            silence_frames = np.where(mean_db < silence_threshold_db)[0]
            
            # Convert frames to time
            hop_length = 512  # Default hop length in librosa.stft
            frame_time = hop_length / sr
            
            # Group consecutive silence frames
            silence_periods = []
            if len(silence_frames) > 0:
                # Initialize with the first frame
                start_frame = silence_frames[0]
                prev_frame = silence_frames[0]
                
                for frame in silence_frames[1:]:
                    # If there's a gap, end the current period and start a new one
                    if frame > prev_frame + 1:
                        end_frame = prev_frame
                        # Convert frames to time
                        start_time = start_frame * frame_time
                        end_time = end_frame * frame_time
                        # Only add if the silence period is long enough
                        if end_time - start_time >= min_silence_duration:
                            silence_periods.append((start_time, end_time))
                        # Start a new period
                        start_frame = frame
                    prev_frame = frame
                
                # Add the last period
                end_frame = prev_frame
                start_time = start_frame * frame_time
                end_time = end_frame * frame_time
                if end_time - start_time >= min_silence_duration:
                    silence_periods.append((start_time, end_time))
            
            return silence_periods
        except Exception as e:
            logger.error("Error detecting silence", error=str(e))
            raise AudioProcessingError(f"Error detecting silence: {str(e)}")

    async def split_audio(self, file_path: Path, output_dir: Path, segment_duration: float = 30.0) -> List[Path]:
        """Split audio file into segments of specified duration.

        Args:
            file_path: Path to the audio file.
            output_dir: Directory to save the segments.
            segment_duration: Duration of each segment in seconds.

        Returns:
            List of paths to the segment files.

        Raises:
            AudioProcessingError: If there's an error splitting the file.
        """
        try:
            # Create output directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)

            # Get audio duration
            duration = await self.get_audio_duration(file_path)

            # Calculate number of segments
            num_segments = int(np.ceil(duration / segment_duration))

            segment_paths = []
            for i in range(num_segments):
                start_time = i * segment_duration
                segment_path = output_dir / f"{file_path.stem}_segment_{i:03d}{file_path.suffix}"

                # Use ffmpeg to extract segment
                (
                    ffmpeg
                    .input(str(file_path), ss=start_time, t=segment_duration)
                    .output(str(segment_path))
                    .overwrite_output()
                    .run(quiet=True, capture_stdout=True, capture_stderr=True)
                )

                segment_paths.append(segment_path)

            return segment_paths
        except ffmpeg.Error as e:
            logger.error("FFmpeg error splitting audio", error=str(e))
            raise AudioProcessingError(f"Error splitting audio: {str(e)}")
        except Exception as e:
            logger.error("Error splitting audio", error=str(e))
            raise AudioProcessingError(f"Error splitting audio: {str(e)}")

    def _get_file_extension(self, filename: str) -> Optional[str]:
        """Get file extension from filename.

        Args:
            filename: Original filename.

        Returns:
            File extension without the dot, or None if no extension.
        """
        if "." not in filename:
            return None
        return filename.rsplit(".", 1)[1].lower()
```

**Исключения для обработки аудио:**
```python
# src/domains/audio/exceptions.py
class AudioProcessingError(Exception):
    """Base exception for audio processing errors."""
    pass


class InvalidAudioFormatError(AudioProcessingError):
    """Exception raised when audio format is not supported."""
    pass


class AudioConversionError(AudioProcessingError):
    """Exception raised when there's an error converting audio."""
    pass


class AudioNormalizationError(AudioProcessingError):
    """Exception raised when there's an error normalizing audio volume."""
    pass
```

**Сущности для аудио:**
```python
# src/domains/audio/entities.py
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import UUID


class AudioFormat(str, Enum):
    """Enum for supported audio formats."""
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    M4A = "m4a"
    WEBM = "webm"


@dataclass
class AudioFile:
    """Entity representing an audio file."""
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
```

**Интеграция с FastAPI для загрузки аудио:**
```python
# src/application/api/routes/audio.py
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.api.dependencies import get_current_user, get_db
from src.domains.audio.exceptions import AudioProcessingError, InvalidAudioFormatError
from src.domains.audio.repositories import AudioRepository
from src.domains.audio.schemas import AudioFileResponse
from src.domains.audio.services.audio_processor import AudioProcessor
from src.domains.audio.services.audio_service import AudioService
from src.domains.user.schemas import UserResponse

router = APIRouter()


@router.post("/", response_model=AudioFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_audio(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    audio_service: AudioService = Depends(),
    audio_processor: AudioProcessor = Depends(),
):
    """Upload a new audio file."""
    try:
        # Save file to temporary location
        content = await file.read()
        
        # Process audio file
        audio_file = await audio_processor.save_audio_file(
            file=content,
            filename=file.filename or "unknown.mp3",
            user_id=current_user.id,
        )
        
        # Save to database
        audio_file = await audio_service.create_audio_file(
            audio_file=audio_file,
            db=db,
        )
        
        return audio_file
    except InvalidAudioFormatError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AudioProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading audio file: {str(e)}",
        )
```

**Тесты для обработки аудио:**
```python
# tests/domains/audio/services/test_audio_processor.py
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import ffmpeg
import pytest

from src.domains.audio.entities import AudioFormat
from src.domains.audio.exceptions import AudioProcessingError, InvalidAudioFormatError
from src.domains.audio.services.audio_processor import AudioProcessor


@pytest.fixture
def audio_processor():
    """Create an AudioProcessor instance with a temporary storage path."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield AudioProcessor(storage_path=Path(temp_dir))


@pytest.fixture
def sample_mp3_file():
    """Create a sample MP3 file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        # Generate a simple MP3 file using ffmpeg
        (
            ffmpeg
            .input("sine=frequency=1000:duration=5", f="lavfi")
            .output(temp_file.name, format="mp3")
            .overwrite_output()
            .run(quiet=True)
        )
        temp_file_path = Path(temp_file.name)
    
    yield temp_file_path
    
    # Clean up
    if temp_file_path.exists():
        temp_file_path.unlink()


@pytest.fixture
def sample_wav_file():
    """Create a sample WAV file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        # Generate a simple WAV file using ffmpeg
        (
            ffmpeg
            .input("sine=frequency=1000:duration=5", f="lavfi")
            .output(temp_file.name, format="wav")
            .overwrite_output()
            .run(quiet=True)
        )
        temp_file_path = Path(temp_file.name)
    
    yield temp_file_path
    
    # Clean up
    if temp_file_path.exists():
        temp_file_path.unlink()


@pytest.mark.asyncio
async def test_validate_audio_file_valid(audio_processor, sample_mp3_file):
    """Test validating a valid audio file."""
    with open(sample_mp3_file, "rb") as f:
        is_valid, error_message = await audio_processor.validate_audio_file(f, sample_mp3_file.name)
    
    assert is_valid is True
    assert error_message is None


@pytest.mark.asyncio
async def test_validate_audio_file_invalid_format(audio_processor):
    """Test validating a file with invalid format."""
    with tempfile.NamedTemporaryFile(suffix=".txt") as temp_file:
        temp_file.write(b"This is not an audio file")
        temp_file.flush()
        temp_file.seek(0)
        
        is_valid, error_message = await audio_processor.validate_audio_file(temp_file, temp_file.name)
    
    assert is_valid is False
    assert "Unsupported file format" in error_message


@pytest.mark.asyncio
async def test_validate_audio_file_too_large(audio_processor, sample_mp3_file):
    """Test validating a file that's too large."""
    with open(sample_mp3_file, "rb") as f:
        # Patch the MAX_FILE_SIZE_BYTES to a small value
        with patch.object(audio_processor, "MAX_FILE_SIZE_BYTES", 100):
            is_valid, error_message = await audio_processor.validate_audio_file(f, sample_mp3_file.name)
    
    assert is_valid is False
    assert "File size exceeds maximum allowed size" in error_message


@pytest.mark.asyncio
async def test_save_audio_file(audio_processor, sample_mp3_file):
    """Test saving an audio file."""
    with open(sample_mp3_file, "rb") as f:
        audio_file = await audio_processor.save_audio_file(f, sample_mp3_file.name, user_id=1)
    
    assert audio_file.id is not None
    assert audio_file.user_id == 1
    assert audio_file.original_filename == sample_mp3_file.name
    assert audio_file.format == AudioFormat.MP3
    assert audio_file.size_bytes > 0
    assert audio_file.duration_seconds is not None
    assert audio_file.path is not None
    assert audio_file.is_valid is True
    
    # Check that the file was actually saved
    assert audio_file.path.exists()


@pytest.mark.asyncio
async def test_convert_to_wav(audio_processor, sample_mp3_file):
    """Test converting an audio file to WAV."""
    wav_path = await audio_processor.convert_to_wav(sample_mp3_file)
    
    assert wav_path.exists()
    assert wav_path.suffix == ".wav"
    
    # Clean up
    wav_path.unlink()


@pytest.mark.asyncio
async def test_normalize_volume(audio_processor, sample_wav_file):
    """Test normalizing audio volume."""
    # Create a copy of the file to normalize
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        with open(sample_wav_file, "rb") as src_file:
            temp_file.write(src_file.read())
        temp_file_path = Path(temp_file.name)
    
    normalized_path = await audio_processor.normalize_volume(temp_file_path)
    
    assert normalized_path.exists()
    
    # Clean up
    normalized_path.unlink()


@pytest.mark.asyncio
async def test_get_audio_duration(audio_processor, sample_mp3_file):
    """Test getting audio duration."""
    duration = await audio_processor.get_audio_duration(sample_mp3_file)
    
    assert duration is not None
    assert duration > 0
    assert duration <= 6  # Should be around 5 seconds


@pytest.mark.asyncio
async def test_detect_silence(audio_processor, sample_mp3_file):
    """Test detecting silence in audio."""
    silence_periods = await audio_processor.detect_silence(sample_mp3_file)
    
    # The test file doesn't have silence, so the list should be empty
    assert isinstance(silence_periods, list)


@pytest.mark.asyncio
async def test_split_audio(audio_processor, sample_mp3_file):
    """Test splitting audio into segments."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        segment_paths = await audio_processor.split_audio(
            sample_mp3_file, output_dir, segment_duration=1.0
        )
        
        assert len(segment_paths) > 0
        for path in segment_paths:
            assert path.exists()
```

#### Схемы данных/API

**Структура обработки аудио:**
```
1. Пользователь загружает аудиофайл через API или Telegram бот
2. Система валидирует формат и размер файла
3. Если файл валиден, он сохраняется в хранилище
4. Система определяет длительность аудио
5. При необходимости, аудио конвертируется в WAV формат для дальнейшей обработки
6. Система нормализует громкость аудио для улучшения качества транскрипции
7. Система детектирует участки тишины для оптимизации обработки
8. Если аудио слишком длинное, оно разбивается на сегменты
9. Подготовленные аудиофайлы передаются для транскрипции и диаризации
```

**Диаграмма последовательности обработки аудио:**
```
User -> API: Upload audio file
API -> AudioProcessor: validate_audio_file()
AudioProcessor -> API: is_valid, error_message

alt is_valid == True
    API -> AudioProcessor: save_audio_file()
    AudioProcessor -> Storage: Save file
    AudioProcessor -> AudioProcessor: get_audio_duration()
    AudioProcessor -> API: AudioFile entity
    
    API -> AudioService: create_audio_file()
    AudioService -> Database: Save AudioFile
    Database -> AudioService: Saved AudioFile
    AudioService -> API: AudioFile response
    
    API -> User: AudioFile response
else
    API -> User: Error response
end
```

### 2. Практическая секция

#### Пошаговые инструкции

1. **Настройка зависимостей:**
   - Установите необходимые пакеты: ffmpeg-python, librosa, pydub
   - Убедитесь, что FFmpeg установлен в системе
   - Настройте пути для хранения аудиофайлов

2. **Реализация валидации аудиофайлов:**
   - Создайте метод для проверки формата файла
   - Добавьте проверку размера файла
   - Реализуйте проверку валидности аудиофайла с помощью FFmpeg

3. **Реализация сохранения аудиофайлов:**
   - Создайте метод для сохранения файла в хранилище
   - Добавьте генерацию уникального идентификатора для файла
   - Реализуйте создание сущности AudioFile

4. **Реализация конвертации форматов:**
   - Создайте метод для конвертации аудио в WAV формат
   - Настройте параметры конвертации (битрейт, частота дискретизации)
   - Добавьте обработку ошибок при конвертации

5. **Реализация нормализации громкости:**
   - Создайте метод для нормализации громкости аудио
   - Настройте параметры нормализации
   - Добавьте обработку ошибок при нормализации

6. **Реализация определения длительности:**
   - Создайте метод для получения длительности аудиофайла
   - Используйте FFmpeg для получения метаданных файла
   - Добавьте обработку ошибок при получении длительности

7. **Реализация детектирования тишины:**
   - Создайте метод для определения участков тишины
   - Настройте параметры детектирования (порог, минимальная длительность)
   - Добавьте обработку ошибок при детектировании тишины

8. **Реализация разбиения аудио на сегменты:**
   - Создайте метод для разбиения аудио на сегменты
   - Настройте параметры разбиения (длительность сегмента)
   - Добавьте обработку ошибок при разбиении

9. **Написание тестов:**
   - Создайте тесты для всех методов обработки аудио
   - Добавьте фикстуры для создания тестовых аудиофайлов
   - Реализуйте проверку результатов обработки

#### Частые ошибки (Common Pitfalls)

1. **Проблемы с FFmpeg:**
   - Отсутствие FFmpeg в системе
   - Неправильные пути к FFmpeg
   - Неправильные параметры команд FFmpeg

2. **Проблемы с форматами аудио:**
   - Неподдерживаемые форматы
   - Поврежденные файлы
   - Файлы без аудиодорожек

3. **Проблемы с обработкой файлов:**
   - Отсутствие прав на запись в директорию хранения
   - Недостаточно места на диске
   - Конфликты имен файлов

4. **Проблемы с многопоточностью:**
   - Одновременный доступ к одному файлу
   - Блокировки при чтении/записи файлов
   - Утечки ресурсов при асинхронной обработке

#### Советы по оптимизации (Performance Tips)

1. **Оптимизация FFmpeg:**
   - Используйте правильные кодеки и параметры для быстрой обработки
   - Применяйте многопоточную обработку для больших файлов
   - Используйте аппаратное ускорение, если доступно

2. **Оптимизация хранения:**
   - Используйте эффективную структуру директорий для хранения файлов
   - Применяйте сжатие для уменьшения размера файлов
   - Реализуйте политику очистки временных файлов

3. **Оптимизация обработки:**
   - Обрабатывайте только необходимые части аудио
   - Используйте детектирование тишины для пропуска пустых участков
   - Применяйте кэширование результатов обработки

### 3. Валидационная секция

#### Чек-лист для самопроверки

- [ ] FFmpeg успешно интегрирован и работает
- [ ] Реализована валидация форматов аудиофайлов
- [ ] Реализована конвертация аудиофайлов в WAV
- [ ] Реализована нормализация громкости аудио
- [ ] Реализовано определение длительности аудиофайлов
- [ ] Реализовано детектирование тишины
- [ ] Реализовано разбиение аудио на сегменты
- [ ] Написаны тесты для всех методов обработки аудио
- [ ] Обработка ошибок реализована и тестируется
- [ ] Код соответствует PEP 8 и включает типизацию
- [ ] Документация к коду добавлена и актуальна

#### Автоматизированные тесты

```python
# tests/domains/audio/test_audio_processor_integration.py
import os
import tempfile
from pathlib import Path

import pytest
import ffmpeg

from src.domains.audio.entities import AudioFormat
from src.domains.audio.exceptions import AudioProcessingError
from src.domains.audio.services.audio_processor import AudioProcessor


@pytest.fixture
def audio_processor():
    """Create an AudioProcessor instance with a temporary storage path."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield AudioProcessor(storage_path=Path(temp_dir))


@pytest.fixture
def create_audio_file():
    """Factory fixture to create audio files of different formats."""
    temp_files = []
    
    def _create_audio_file(format="mp3", duration=5):
        suffix = f".{format}"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            # Generate a simple audio file using ffmpeg
            (
                ffmpeg
                .input(f"sine=frequency=1000:duration={duration}", f="lavfi")
                .output(temp_file.name, format=format)
                .overwrite_output()
                .run(quiet=True)
            )
            temp_file_path = Path(temp_file.name)
            temp_files.append(temp_file_path)
            return temp_file_path
    
    yield _create_audio_file
    
    # Clean up
    for file_path in temp_files:
        if file_path.exists():
            file_path.unlink()


@pytest.mark.asyncio
async def test_end_to_end_audio_processing(audio_processor, create_audio_file):
    """Test the complete audio processing workflow."""
    # Create a test MP3 file
    mp3_file = create_audio_file(format="mp3", duration=10)
    
    # 1. Validate the file
    with open(mp3_file, "rb") as f:
        is_valid, error_message = await audio_processor.validate_audio_file(f, mp3_file.name)
    
    assert is_valid is True
    assert error_message is None
    
    # 2. Save the file
    with open(mp3_file, "rb") as f:
        audio_file = await audio_processor.save_audio_file(f, mp3_file.name, user_id=1)
    
    assert audio_file.id is not None
    assert audio_file.format == AudioFormat.MP3
    assert audio_file.is_valid is True
    
    # 3. Convert to WAV
    wav_path = await audio_processor.convert_to_wav(audio_file.path)
    
    assert wav_path.exists()
    assert wav_path.suffix == ".wav"
    
    # 4. Normalize volume
    normalized_path = await audio_processor.normalize_volume(wav_path)
    
    assert normalized_path.exists()
    
    # 5. Get duration
    duration = await audio_processor.get_audio_duration(normalized_path)
    
    assert duration is not None
    assert duration > 0
    
    # 6. Detect silence
    silence_periods = await audio_processor.detect_silence(normalized_path)
    
    assert isinstance(silence_periods, list)
    
    # 7. Split audio
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        segment_paths = await audio_processor.split_audio(
            normalized_path, output_dir, segment_duration=2.0
        )
        
        assert len(segment_paths) > 0
        for path in segment_paths:
            assert path.exists()
            
            # Check that each segment can be processed
            segment_duration = await audio_processor.get_audio_duration(path)
            assert segment_duration > 0
            assert segment_duration <= 2.0 or segment_duration - 2.0 < 0.1  # Allow small margin of error


@pytest.mark.asyncio
async def test_processing_different_formats(audio_processor, create_audio_file):
    """Test processing different audio formats."""
    formats = ["mp3", "wav", "ogg"]
    
    for format in formats:
        # Create a test file
        audio_file_path = create_audio_file(format=format)
        
        # Validate the file
        with open(audio_file_path, "rb") as f:
            is_valid, error_message = await audio_processor.validate_audio_file(f, audio_file_path.name)
        
        assert is_valid is True, f"Format {format} should be valid"
        
        # Convert to WAV
        wav_path = await audio_processor.convert_to_wav(audio_file_path)
        
        assert wav_path.exists(), f"Failed to convert {format} to WAV"
        assert wav_path.suffix == ".wav"
        
        # Clean up
        if wav_path.exists():
            wav_path.unlink()
```

#### Критерии для ручного тестирования

1. **Проверка валидации форматов:**
   - Загрузите файлы различных форматов (mp3, wav, ogg, m4a, webm)
   - Попробуйте загрузить файл неподдерживаемого формата (txt, pdf)
   - Попробуйте загрузить файл слишком большого размера

2. **Проверка конвертации:**
   - Конвертируйте файлы различных форматов в WAV
   - Проверьте качество конвертированных файлов
   - Убедитесь, что метаданные сохраняются при конвертации

3. **Проверка нормализации громкости:**
   - Нормализуйте аудиофайлы с разным уровнем громкости
   - Сравните громкость до и после нормализации
   - Проверьте качество звука после нормализации

4. **Проверка определения длительности:**
   - Определите длительность файлов различной длины
   - Сравните полученную длительность с фактической
   - Проверьте точность определения длительности

5. **Проверка детектирования тишины:**
   - Детектируйте тишину в файлах с различными уровнями шума
   - Проверьте точность определения участков тишины
   - Убедитесь, что короткие паузы не определяются как тишина

6. **Проверка разбиения на сегменты:**
   - Разбейте файлы различной длины на сегменты
   - Проверьте, что все сегменты имеют правильную длительность
   - Убедитесь, что при объединении сегментов получается исходный файл

## Вопросы к постановщику задачи
1. Какие дополнительные форматы аудио нужно поддерживать помимо указанных?
2. Требуется ли реализация дополнительных методов обработки аудио (шумоподавление, эквализация)?
3. Какие конкретные параметры нормализации громкости нужно использовать?
4. Требуется ли сохранение метаданных аудиофайлов (исполнитель, название, альбом)?
5. Какие ограничения по ресурсам (CPU, RAM) существуют для обработки аудио?