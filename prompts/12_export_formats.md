# Фаза 3, День 12: Экспорт форматов: DOCX, SRT, JSON с правильным форматированием

## Цель (Definition of Done)
- Реализован экспорт транскрипций в формат DOCX с форматированием спикеров и тайм-кодов
- Реализован экспорт в формат SRT для использования в качестве субтитров
- Реализован экспорт в формат JSON с полными метаданными
- Реализован экспорт в простой текстовый формат для быстрого копирования
- Добавлена возможность выбора формата экспорта пользователем
- Реализована система хранения и доступа к экспортированным файлам

## Ссылки на документацию
- [python-docx Documentation](https://python-docx.readthedocs.io/en/latest/)
- [pysrt Documentation](https://github.com/byroot/pysrt)
- [JSON in Python](https://docs.python.org/3/library/json.html)
- [NATS Object Storage](https://docs.nats.io/nats-concepts/jetstream/obj_store)
- [FastAPI File Response](https://fastapi.tiangolo.com/advanced/custom-response/#fileresponse)

---

## 1. Техническая секция

### Описание
В этом разделе мы реализуем функциональность экспорта результатов транскрипции в различные форматы. Каждый формат имеет свои особенности и требует специфического подхода к форматированию:

1. **DOCX**: Документ Word с форматированием спикеров, тайм-кодами и стилями
2. **SRT**: Формат субтитров с временными метками для использования в видеоредакторах
3. **JSON**: Полные метаданные транскрипции, включая информацию о спикерах, уверенности распознавания и т.д.
4. **Plain Text**: Простой текстовый формат для быстрого копирования

Мы также реализуем систему хранения экспортированных файлов и API для их скачивания.

### Примеры кода

#### Сервис экспорта

```python
# src/domains/export/services.py
import json
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, List, Optional, BinaryIO, Tuple

import docx
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import pysrt

from src.domains.export.schemas import ExportFormat, ExportRequest, ExportResult
from src.domains.transcription.schemas import TranscriptionResult, TranscriptionSegment
from src.infrastructure.storage.object_storage import ObjectStorage

class ExportService:
    """Service for exporting transcription results to different formats."""
    
    def __init__(self, object_storage: ObjectStorage):
        self.object_storage = object_storage
    
    async def export_transcription(self, request: ExportRequest) -> ExportResult:
        """Export transcription to specified format(s)."""
        result = ExportResult(
            task_id=request.task_id,
            formats={},
            created_at=datetime.utcnow()
        )
        
        # Get transcription result
        transcription = request.transcription
        
        # Export to requested formats
        formats_to_export = request.formats or [ExportFormat.all]
        
        # If "all" is specified, export to all formats
        if ExportFormat.all in formats_to_export:
            formats_to_export = [
                ExportFormat.docx,
                ExportFormat.srt,
                ExportFormat.json,
                ExportFormat.text
            ]
        
        # Export to each format
        for export_format in formats_to_export:
            if export_format == ExportFormat.all:
                continue
                
            file_path, file_size = await self._export_to_format(
                transcription=transcription,
                export_format=export_format,
                task_id=request.task_id,
                metadata=request.metadata
            )
            
            result.formats[export_format] = {
                "file_path": file_path,
                "file_size": file_size,
                "download_url": await self.object_storage.get_download_url(file_path)
            }
        
        return result
    
    async def _export_to_format(
        self,
        transcription: TranscriptionResult,
        export_format: ExportFormat,
        task_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, int]:
        """Export transcription to a specific format and store in object storage."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Export based on format
            if export_format == ExportFormat.docx:
                file_content = self._export_to_docx(transcription, metadata)
                file_extension = "docx"
            elif export_format == ExportFormat.srt:
                file_content = self._export_to_srt(transcription)
                file_extension = "srt"
            elif export_format == ExportFormat.json:
                file_content = self._export_to_json(transcription, metadata)
                file_extension = "json"
            elif export_format == ExportFormat.text:
                file_content = self._export_to_text(transcription)
                file_extension = "txt"
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
            
            # Write content to temporary file
            with open(temp_path, "wb") as f:
                f.write(file_content)
            
            # Get file size
            file_size = os.path.getsize(temp_path)
            
            # Generate storage path
            storage_path = f"exports/{task_id}/{export_format.value}.{file_extension}"
            
            # Upload to object storage
            with open(temp_path, "rb") as f:
                await self.object_storage.upload_file(storage_path, f)
            
            return storage_path, file_size
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def _export_to_docx(
        self,
        transcription: TranscriptionResult,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Export transcription to DOCX format."""
        # Create document
        doc = docx.Document()
        
        # Add title
        title = doc.add_heading("Транскрипция", level=1)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add metadata
        if metadata:
            metadata_para = doc.add_paragraph()
            metadata_para.add_run("Метаданные:").bold = True
            
            # Add file info
            if "file_name" in metadata:
                metadata_para.add_run(f"\nФайл: {metadata['file_name']}")
            if "duration" in metadata:
                duration_mins = metadata["duration"] // 60
                duration_secs = metadata["duration"] % 60
                metadata_para.add_run(f"\nДлительность: {duration_mins}:{duration_secs:02d}")
            if "created_at" in metadata:
                created_at = metadata["created_at"]
                if isinstance(created_at, str):
                    metadata_para.add_run(f"\nДата создания: {created_at}")
                else:
                    metadata_para.add_run(f"\nДата создания: {created_at.strftime('%d.%m.%Y %H:%M')}")
            
            # Add model info
            if "model" in metadata:
                metadata_para.add_run(f"\nМодель: {metadata['model']}")
            if "language" in metadata:
                metadata_para.add_run(f"\nЯзык: {metadata['language']}")
            
            # Add separator
            doc.add_paragraph()
        
        # Define speaker styles (up to 10 speakers)
        speaker_styles = [
            {"color": RGBColor(0, 112, 192), "bold": True},    # Blue
            {"color": RGBColor(255, 0, 0), "bold": True},      # Red
            {"color": RGBColor(0, 176, 80), "bold": True},     # Green
            {"color": RGBColor(112, 48, 160), "bold": True},   # Purple
            {"color": RGBColor(255, 192, 0), "bold": True},    # Orange
            {"color": RGBColor(91, 155, 213), "bold": True},   # Light Blue
            {"color": RGBColor(255, 128, 0), "bold": True},    # Dark Orange
            {"color": RGBColor(146, 208, 80), "bold": True},   # Light Green
            {"color": RGBColor(192, 0, 0), "bold": True},      # Dark Red
            {"color": RGBColor(0, 32, 96), "bold": True},      # Dark Blue
        ]
        
        # Add transcription segments
        for segment in transcription.segments:
            # Create paragraph for segment
            para = doc.add_paragraph()
            
            # Add timestamp
            start_time = self._format_timestamp(segment.start)
            end_time = self._format_timestamp(segment.end)
            timestamp_run = para.add_run(f"[{start_time} - {end_time}] ")
            timestamp_run.font.size = Pt(8)
            timestamp_run.font.color.rgb = RGBColor(128, 128, 128)
            
            # Add speaker if available
            if segment.speaker is not None:
                speaker_idx = min(segment.speaker, len(speaker_styles) - 1)
                style = speaker_styles[speaker_idx]
                speaker_run = para.add_run(f"Спикер {segment.speaker + 1}: ")
                speaker_run.bold = style["bold"]
                speaker_run.font.color.rgb = style["color"]
            
            # Add text
            text_run = para.add_run(segment.text)
        
        # Save document to bytes
        with tempfile.BytesIO() as output:
            doc.save(output)
            return output.getvalue()
    
    def _export_to_srt(self, transcription: TranscriptionResult) -> bytes:
        """Export transcription to SRT format."""
        # Create SRT file
        subs = pysrt.SubRipFile()
        
        # Add segments as subtitles
        for i, segment in enumerate(transcription.segments):
            # Create subtitle
            sub = pysrt.SubRipItem()
            sub.index = i + 1
            
            # Set start and end times
            start_time = self._seconds_to_srt_time(segment.start)
            end_time = self._seconds_to_srt_time(segment.end)
            sub.start = start_time
            sub.end = end_time
            
            # Set text (with speaker if available)
            if segment.speaker is not None:
                sub.text = f"Спикер {segment.speaker + 1}: {segment.text}"
            else:
                sub.text = segment.text
            
            # Add to file
            subs.append(sub)
        
        # Convert to string and then to bytes
        return str(subs).encode("utf-8")
    
    def _export_to_json(
        self,
        transcription: TranscriptionResult,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Export transcription to JSON format with full metadata."""
        # Create JSON structure
        result = {
            "text": transcription.text,
            "segments": [segment.dict() for segment in transcription.segments],
            "metadata": metadata or {}
        }
        
        # Convert to JSON string and then to bytes
        return json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
    
    def _export_to_text(self, transcription: TranscriptionResult) -> bytes:
        """Export transcription to plain text format."""
        # Create text with segments and speakers
        lines = []
        
        for segment in transcription.segments:
            # Format timestamp
            start_time = self._format_timestamp(segment.start)
            end_time = self._format_timestamp(segment.end)
            timestamp = f"[{start_time} - {end_time}]"
            
            # Format speaker if available
            if segment.speaker is not None:
                speaker = f"Спикер {segment.speaker + 1}: "
            else:
                speaker = ""
            
            # Add line
            lines.append(f"{timestamp} {speaker}{segment.text}")
        
        # Join lines and convert to bytes
        return "\n".join(lines).encode("utf-8")
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as MM:SS."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def _seconds_to_srt_time(self, seconds: float) -> pysrt.SubRipTime:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return pysrt.SubRipTime(hours, minutes, seconds, milliseconds)
```

#### Схемы данных для экспорта

```python
# src/domains/export/schemas.py
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field

from src.domains.transcription.schemas import TranscriptionResult

class ExportFormat(str, Enum):
    """Supported export formats."""
    docx = "docx"
    srt = "srt"
    json = "json"
    text = "text"
    all = "all"

class ExportRequest(BaseModel):
    """Request for exporting transcription."""
    task_id: str = Field(..., description="Task ID")
    transcription: TranscriptionResult = Field(..., description="Transcription result")
    formats: Optional[List[ExportFormat]] = Field(None, description="Export formats")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class ExportFormatInfo(BaseModel):
    """Information about exported file."""
    file_path: str = Field(..., description="Path to file in storage")
    file_size: int = Field(..., description="File size in bytes")
    download_url: str = Field(..., description="Download URL")

class ExportResult(BaseModel):
    """Result of export operation."""
    task_id: str = Field(..., description="Task ID")
    formats: Dict[ExportFormat, ExportFormatInfo] = Field(
        default_factory=dict,
        description="Exported formats with file info"
    )
    created_at: datetime = Field(..., description="Export timestamp")
```

#### Интеграция с хранилищем объектов

```python
# src/infrastructure/storage/object_storage.py
import io
from typing import BinaryIO, Optional, Dict, Any

import nats
from nats.js.api import ObjectStoreConfig
from nats.js.object_store import ObjectStore

from src.config import settings

class ObjectStorage:
    """Service for storing and retrieving files using NATS Object Storage."""
    
    def __init__(self):
        self._nc = None
        self._js = None
        self._object_stores = {}
    
    async def connect(self):
        """Connect to NATS server and initialize object stores."""
        if self._nc is None:
            self._nc = await nats.connect(settings.NATS_URL)
            self._js = self._nc.jetstream()
            
            # Initialize default object store
            await self._get_or_create_object_store("transcription")
    
    async def close(self):
        """Close NATS connection."""
        if self._nc:
            await self._nc.close()
            self._nc = None
            self._js = None
            self._object_stores = {}
    
    async def _get_or_create_object_store(self, name: str) -> ObjectStore:
        """Get or create an object store."""
        if name in self._object_stores:
            return self._object_stores[name]
        
        try:
            # Try to get existing object store
            obj_store = await self._js.object_store(name)
        except Exception:
            # Create new object store if it doesn't exist
            config = ObjectStoreConfig(
                name=name,
                storage="file",
                max_bytes=settings.OBJECT_STORE_MAX_BYTES
            )
            obj_store = await self._js.create_object_store(config)
        
        self._object_stores[name] = obj_store
        return obj_store
    
    async def upload_file(
        self,
        path: str,
        file: BinaryIO,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Upload file to object storage."""
        await self.connect()
        
        # Get object store name and object name from path
        store_name, obj_name = self._parse_path(path)
        obj_store = await self._get_or_create_object_store(store_name)
        
        # Upload file
        await obj_store.put(obj_name, file.read(), metadata=metadata)
        
        return path
    
    async def download_file(self, path: str) -> bytes:
        """Download file from object storage."""
        await self.connect()
        
        # Get object store name and object name from path
        store_name, obj_name = self._parse_path(path)
        obj_store = await self._get_or_create_object_store(store_name)
        
        # Download file
        obj_info = await obj_store.get(obj_name)
        return obj_info.data
    
    async def get_download_url(self, path: str) -> str:
        """Get download URL for file."""
        # In a real implementation, this would generate a signed URL
        # For simplicity, we'll just return a path to our API endpoint
        return f"{settings.API_BASE_URL}/api/v1/exports/download?path={path}"
    
    async def delete_file(self, path: str) -> bool:
        """Delete file from object storage."""
        await self.connect()
        
        # Get object store name and object name from path
        store_name, obj_name = self._parse_path(path)
        obj_store = await self._get_or_create_object_store(store_name)
        
        # Delete file
        try:
            await obj_store.delete(obj_name)
            return True
        except Exception:
            return False
    
    def _parse_path(self, path: str) -> tuple:
        """Parse path into object store name and object name."""
        parts = path.split("/", 1)
        if len(parts) == 1:
            return "transcription", parts[0]
        return parts[0], parts[1]
```

#### API для скачивания экспортированных файлов

```python
# src/api/v1/endpoints/exports.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
import tempfile
import os

from src.domains.export.schemas import ExportFormat, ExportRequest, ExportResult
from src.domains.export.services import ExportService
from src.infrastructure.storage.object_storage import ObjectStorage
from src.api.dependencies import get_object_storage

router = APIRouter()

@router.post("/", response_model=ExportResult)
async def export_transcription(
    request: ExportRequest,
    export_service: ExportService = Depends(lambda: ExportService(get_object_storage()))
) -> ExportResult:
    """Export transcription to specified formats."""
    try:
        result = await export_service.export_transcription(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/download")
async def download_export(
    path: str = Query(..., description="Path to file in storage"),
    object_storage: ObjectStorage = Depends(get_object_storage)
) -> FileResponse:
    """Download exported file."""
    try:
        # Get file data
        file_data = await object_storage.download_file(path)
        
        # Determine file name and content type
        file_name = os.path.basename(path)
        content_type = _get_content_type(file_name)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file_name}") as temp_file:
            temp_path = temp_file.name
            temp_file.write(file_data)
        
        # Return file response
        return FileResponse(
            path=temp_path,
            filename=file_name,
            media_type=content_type,
            background=_cleanup_temp_file(temp_path)
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")

def _get_content_type(file_name: str) -> str:
    """Get content type based on file extension."""
    if file_name.endswith(".docx"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif file_name.endswith(".srt"):
        return "application/x-subrip"
    elif file_name.endswith(".json"):
        return "application/json"
    elif file_name.endswith(".txt"):
        return "text/plain"
    return "application/octet-stream"

async def _cleanup_temp_file(file_path: str):
    """Clean up temporary file after response is sent."""
    try:
        os.unlink(file_path)
    except Exception:
        pass
```

#### Интеграция с сервисом транскрипции

```python
# src/domains/transcription/services.py
# ... existing code ...

from src.domains.export.services import ExportService
from src.domains.export.schemas import ExportFormat, ExportRequest

class TranscriptionService:
    # ... existing methods ...
    
    async def export_transcription(
        self,
        task_id: str,
        formats: Optional[List[ExportFormat]] = None
    ) -> Dict[str, str]:
        """Export transcription to specified formats and return download URLs."""
        # Get transcription result
        task = await self.get_task(task_id)
        if not task or task.status != "completed":
            raise ValueError(f"Task {task_id} not completed or not found")
        
        # Get transcription result
        transcription = task.result
        
        # Prepare metadata
        metadata = {
            "file_name": task.file_name,
            "duration": task.duration,
            "created_at": task.created_at,
            "model": task.model,
            "language": task.language,
            "speakers_count": task.speakers_count
        }
        
        # Create export request
        request = ExportRequest(
            task_id=task_id,
            transcription=transcription,
            formats=formats,
            metadata=metadata
        )
        
        # Export transcription
        export_service = ExportService(self.object_storage)
        result = await export_service.export_transcription(request)
        
        # Return download URLs
        return {
            format_name.value: format_info.download_url
            for format_name, format_info in result.formats.items()
        }
    
    async def get_download_links(self, task_id: str) -> Dict[str, str]:
        """Get download links for all available export formats."""
        return await self.export_transcription(
            task_id=task_id,
            formats=[ExportFormat.all]
        )
```

#### Обновление бота для поддержки экспорта

```python
# src/bot/dialogs/result.py
from typing import Any, Dict

from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, Select, Cancel
from aiogram_dialog.widgets.text import Const, Format

from src.bot.states import ResultState, MainMenuState
from src.domains.transcription.services import TranscriptionService

async def result_getter(dialog_manager: DialogManager, 
                       transcription_service: TranscriptionService, **kwargs):
    """Get transcription result."""
    task_id = dialog_manager.dialog_data.get("task_id")
    if not task_id:
        return {
            "text": "Результат не найден",
            "has_result": False
        }
    
    # Get task details
    task = await transcription_service.get_task_details(task_id)
    if not task or task.get("status") != "completed":
        return {
            "text": "Результат не найден или задача не завершена",
            "has_result": False
        }
    
    # Get transcription text
    result = task.get("result", {})
    text = result.get("text", "")
    
    # Truncate text if too long for Telegram message
    if len(text) > 3000:
        text = text[:3000] + "...\n\n(Текст слишком длинный, скачайте полный результат)"
    
    return {
        "text": text,
        "has_result": True,
        "task_id": task_id
    }

async def on_export_selected(callback: CallbackQuery, button: Button, 
                            dialog_manager: DialogManager,
                            transcription_service: TranscriptionService):
    """Handler for exporting result."""
    task_id = dialog_manager.dialog_data.get("task_id")
    if not task_id:
        await callback.answer("Результат не найден")
        return
    
    # Get download links
    download_links = await transcription_service.get_download_links(task_id)
    
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

# Result window
result_window = Window(
    Const("📝 Результат транскрипции:"),
    Format("{text}"),
    Row(
        Button(
            Const("📥 Экспортировать"),
            id="export_result",
            on_click=on_export_selected,
            when="has_result"
        ),
    ),
    Row(
        Button(
            Const("🔙 В главное меню"),
            id="back_to_menu",
            on_click=lambda c, b, m: m.start(MainMenuState.main)
        )
    ),
    state=ResultState.view,
    getter=result_getter
)

# Create dialog
result_dialog = Dialog(result_window)
```

### Конфигурации

#### Настройка зависимостей для экспорта

```python
# src/api/dependencies.py
from fastapi import Depends

from src.domains.export.services import ExportService
from src.infrastructure.storage.object_storage import ObjectStorage

# Singleton instance of ObjectStorage
_object_storage = None

def get_object_storage() -> ObjectStorage:
    """Get or create ObjectStorage instance."""
    global _object_storage
    if _object_storage is None:
        _object_storage = ObjectStorage()
    return _object_storage

def get_export_service(
    object_storage: ObjectStorage = Depends(get_object_storage)
) -> ExportService:
    """Get ExportService instance."""
    return ExportService(object_storage)
```

#### Настройка маршрутов API

```python
# src/api/v1/router.py
from fastapi import APIRouter

from src.api.v1.endpoints import transcriptions, tasks, exports

api_router = APIRouter()
api_router.include_router(transcriptions.router, prefix="/transcriptions", tags=["transcriptions"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(exports.router, prefix="/exports", tags=["exports"])
```

### Схемы данных/API

#### Обновление схем транскрипции

```python
# src/domains/transcription/schemas.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TranscriptionSegment(BaseModel):
    """Model for a transcription segment."""
    id: int = Field(..., description="Segment ID")
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Transcribed text")
    speaker: Optional[int] = Field(None, description="Speaker ID (0-based)")
    confidence: Optional[float] = Field(None, description="Confidence score")

class TranscriptionResult(BaseModel):
    """Model for transcription result."""
    text: str = Field(..., description="Full transcribed text")
    segments: List[TranscriptionSegment] = Field(..., description="Transcription segments")
    language: Optional[str] = Field(None, description="Detected language")
    speakers_count: Optional[int] = Field(None, description="Number of speakers detected")

class TranscriptionTask(BaseModel):
    """Model for transcription task."""
    id: str = Field(..., description="Task ID")
    user_id: int = Field(..., description="User ID")
    file_id: str = Field(..., description="File ID")
    file_name: Optional[str] = Field(None, description="File name")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    model: str = Field(..., description="Transcription model")
    language: str = Field(..., description="Language code or 'auto'")
    diarization: bool = Field(True, description="Whether to perform diarization")
    status: str = Field(..., description="Task status")
    progress: float = Field(0.0, description="Progress (0.0-1.0)")
    result: Optional[TranscriptionResult] = Field(None, description="Transcription result")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    speakers_count: Optional[int] = Field(None, description="Number of speakers detected")
```

## 2. Практическая секция

### Пошаговые инструкции

1. **Настройка хранилища объектов**
   - Создайте модуль `src/infrastructure/storage/object_storage.py`
   - Реализуйте класс `ObjectStorage` для работы с NATS Object Storage
   - Добавьте методы для загрузки, скачивания и удаления файлов

2. **Реализация сервиса экспорта**
   - Создайте модуль `src/domains/export/services.py`
   - Реализуйте класс `ExportService` с методами для экспорта в разные форматы
   - Добавьте поддержку форматов DOCX, SRT, JSON и Text

3. **Реализация экспорта в DOCX**
   - Установите библиотеку python-docx: `pip install python-docx`
   - Реализуйте метод `_export_to_docx` в `ExportService`
   - Добавьте форматирование спикеров, тайм-кодов и стилей

4. **Реализация экспорта в SRT**
   - Установите библиотеку pysrt: `pip install pysrt`
   - Реализуйте метод `_export_to_srt` в `ExportService`
   - Добавьте корректное форматирование временных меток

5. **Реализация экспорта в JSON и Text**
   - Реализуйте методы `_export_to_json` и `_export_to_text` в `ExportService`
   - Добавьте полные метаданные в JSON-экспорт
   - Обеспечьте читаемый формат для текстового экспорта

6. **Создание API для экспорта**
   - Создайте модуль `src/api/v1/endpoints/exports.py`
   - Реализуйте эндпоинты для экспорта и скачивания файлов
   - Добавьте обработку ошибок и валидацию запросов

7. **Интеграция с сервисом транскрипции**
   - Обновите `TranscriptionService` для поддержки экспорта
   - Добавьте методы для получения ссылок на скачивание
   - Обеспечьте передачу метаданных в экспортируемые файлы

8. **Обновление пользовательского интерфейса**
   - Добавьте диалог для просмотра результатов транскрипции
   - Реализуйте кнопки для экспорта в разные форматы
   - Обеспечьте отправку ссылок на скачивание пользователю

### Частые ошибки (Common Pitfalls)

1. **Проблемы с кодировкой текста**
   - Всегда используйте UTF-8 для текстовых файлов
   - Проверяйте корректность кодировки при работе с русским языком
   - Используйте `ensure_ascii=False` при сериализации JSON

2. **Утечки памяти при работе с большими файлами**
   - Используйте потоковую обработку для больших файлов
   - Не загружайте весь файл в память, если это не необходимо
   - Правильно закрывайте файловые дескрипторы

3. **Некорректное форматирование временных меток**
   - Учитывайте разные форматы времени для разных форматов экспорта
   - Проверяйте корректность конвертации секунд в формат HH:MM:SS,mmm
   - Обрабатывайте граничные случаи (0 секунд, очень длинные аудио)

4. **Проблемы с доступом к файлам**
   - Используйте временные файлы для промежуточного хранения
   - Правильно обрабатывайте исключения при работе с файловой системой
   - Очищайте временные файлы после использования

5. **Ошибки при работе с NATS Object Storage**
   - Обрабатывайте ошибки соединения с NATS
   - Проверяйте существование объектов перед их использованием
   - Используйте повторные попытки для операций с хранилищем

### Советы по оптимизации (Performance Tips)

1. **Оптимизация работы с DOCX**
   - Используйте стили вместо прямого форматирования
   - Минимизируйте количество запросов к объектам документа
   - Предварительно создавайте и кешируйте часто используемые стили

2. **Эффективная работа с хранилищем объектов**
   - Используйте пулинг соединений для NATS
   - Группируйте операции для уменьшения количества запросов
   - Реализуйте кеширование для часто запрашиваемых файлов

3. **Оптимизация генерации SRT**
   - Предварительно рассчитывайте временные метки
   - Используйте буферизацию для построчной записи
   - Избегайте повторного создания объектов SubRipTime

4. **Улучшение производительности API**
   - Используйте асинхронные операции для работы с файлами
   - Реализуйте потоковую передачу больших файлов
   - Добавьте кеширование для часто запрашиваемых результатов

5. **Оптимизация пользовательского опыта**
   - Предварительно генерируйте экспорты для всех форматов
   - Показывайте прогресс экспорта для больших файлов
   - Реализуйте фоновую генерацию экспортов

## 3. Валидационная секция

### Чек-лист для самопроверки

- [ ] Реализован экспорт в формат DOCX с корректным форматированием
- [ ] Реализован экспорт в формат SRT с правильными временными метками
- [ ] Реализован экспорт в формат JSON с полными метаданными
- [ ] Реализован экспорт в текстовый формат с читаемой структурой
- [ ] Настроено хранилище объектов для хранения экспортированных файлов
- [ ] Создан API для экспорта и скачивания файлов
- [ ] Интегрирован сервис экспорта с сервисом транскрипции
- [ ] Обновлен пользовательский интерфейс для поддержки экспорта
- [ ] Добавлена обработка ошибок и валидация запросов
- [ ] Реализованы тесты для проверки функциональности экспорта

### Автоматизированные тесты

```python
# tests/domains/export/test_export_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import os

from src.domains.export.services import ExportService
from src.domains.export.schemas import ExportFormat, ExportRequest
from src.domains.transcription.schemas import TranscriptionResult, TranscriptionSegment

@pytest.fixture
def mock_object_storage():
    """Mock object storage."""
    storage = AsyncMock()
    storage.upload_file.return_value = "exports/test-task/docx.docx"
    storage.get_download_url.return_value = "http://example.com/download?path=exports/test-task/docx.docx"
    return storage

@pytest.fixture
def sample_transcription():
    """Sample transcription result."""
    return TranscriptionResult(
        text="This is a test transcription. Another speaker here.",
        segments=[
            TranscriptionSegment(
                id=1,
                start=0.0,
                end=3.5,
                text="This is a test transcription.",
                speaker=0,
                confidence=0.95
            ),
            TranscriptionSegment(
                id=2,
                start=4.0,
                end=6.0,
                text="Another speaker here.",
                speaker=1,
                confidence=0.9
            )
        ],
        language="en",
        speakers_count=2
    )

@pytest.fixture
def export_request(sample_transcription):
    """Sample export request."""
    return ExportRequest(
        task_id="test-task",
        transcription=sample_transcription,
        formats=[ExportFormat.docx, ExportFormat.srt, ExportFormat.json, ExportFormat.text],
        metadata={
            "file_name": "test.mp3",
            "duration": 6.0,
            "created_at": "2023-01-01T12:00:00",
            "model": "whisper-large-v3",
            "language": "en",
            "speakers_count": 2
        }
    )

@pytest.mark.asyncio
async def test_export_to_docx(mock_object_storage, export_request):
    """Test export to DOCX format."""
    # Create service
    service = ExportService(mock_object_storage)
    
    # Mock _export_to_format to avoid actual file operations
    with patch.object(service, '_export_to_format', return_value=("exports/test-task/docx.docx", 1024)):
        # Export transcription
        result = await service.export_transcription(export_request)
        
        # Check result
        assert ExportFormat.docx in result.formats
        assert result.formats[ExportFormat.docx].file_path == "exports/test-task/docx.docx"
        assert result.formats[ExportFormat.docx].file_size == 1024
        assert result.formats[ExportFormat.docx].download_url == "http://example.com/download?path=exports/test-task/docx.docx"

@pytest.mark.asyncio
async def test_export_all_formats(mock_object_storage, export_request):
    """Test export to all formats."""
    # Create service
    service = ExportService(mock_object_storage)
    
    # Set formats to "all"
    export_request.formats = [ExportFormat.all]
    
    # Mock _export_to_format to avoid actual file operations
    with patch.object(service, '_export_to_format', return_value=("exports/test-task/format.ext", 1024)):
        # Export transcription
        result = await service.export_transcription(export_request)
        
        # Check result
        assert ExportFormat.docx in result.formats
        assert ExportFormat.srt in result.formats
        assert ExportFormat.json in result.formats
        assert ExportFormat.text in result.formats

def test_format_timestamp():
    """Test timestamp formatting."""
    service = ExportService(None)
    
    # Test various timestamps
    assert service._format_timestamp(0) == "00:00"
    assert service._format_timestamp(30) == "00:30"
    assert service._format_timestamp(65) == "01:05"
    assert service._format_timestamp(3600) == "60:00"

def test_seconds_to_srt_time():
    """Test conversion to SRT time format."""
    service = ExportService(None)
    
    # Test various timestamps
    srt_time = service._seconds_to_srt_time(0)
    assert str(srt_time) == "00:00:00,000"
    
    srt_time = service._seconds_to_srt_time(30.5)
    assert str(srt_time) == "00:00:30,500"
    
    srt_time = service._seconds_to_srt_time(65.25)
    assert str(srt_time) == "00:01:05,250"
    
    srt_time = service._seconds_to_srt_time(3600.75)
    assert str(srt_time) == "01:00:00,750"

# tests/api/v1/endpoints/test_exports.py
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from src.api.v1.endpoints.exports import router
from src.domains.export.schemas import ExportFormat, ExportRequest, ExportResult, ExportFormatInfo
from src.main import app

@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)

@pytest.fixture
def mock_export_service():
    """Mock export service."""
    service = AsyncMock()
    service.export_transcription.return_value = ExportResult(
        task_id="test-task",
        formats={
            ExportFormat.docx: ExportFormatInfo(
                file_path="exports/test-task/docx.docx",
                file_size=1024,
                download_url="http://example.com/download?path=exports/test-task/docx.docx"
            ),
            ExportFormat.srt: ExportFormatInfo(
                file_path="exports/test-task/srt.srt",
                file_size=512,
                download_url="http://example.com/download?path=exports/test-task/srt.srt"
            )
        },
        created_at="2023-01-01T12:00:00"
    )
    return service

@pytest.mark.asyncio
async def test_export_transcription(client, mock_export_service):
    """Test export transcription endpoint."""
    # Mock dependencies
    with patch("src.api.v1.endpoints.exports.ExportService", return_value=mock_export_service):
        # Create request data
        request_data = {
            "task_id": "test-task",
            "transcription": {
                "text": "Test transcription",
                "segments": [
                    {
                        "id": 1,
                        "start": 0.0,
                        "end": 3.0,
                        "text": "Test transcription",
                        "speaker": 0,
                        "confidence": 0.95
                    }
                ]
            },
            "formats": ["docx", "srt"],
            "metadata": {
                "file_name": "test.mp3",
                "duration": 3.0
            }
        }
        
        # Send request
        response = client.post("/api/v1/exports/", json=request_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task"
        assert "docx" in data["formats"]
        assert "srt" in data["formats"]
        assert data["formats"]["docx"]["download_url"] == "http://example.com/download?path=exports/test-task/docx.docx"

@pytest.mark.asyncio
async def test_download_export(client):
    """Test download export endpoint."""
    # Mock object storage
    mock_storage = AsyncMock()
    mock_storage.download_file.return_value = b"Test file content"
    
    # Mock dependencies
    with patch("src.api.v1.endpoints.exports.get_object_storage", return_value=mock_storage):
        # Send request
        response = client.get("/api/v1/exports/download?path=exports/test-task/docx.docx")
        
        # Check response
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert response.headers["content-disposition"] == 'attachment; filename="docx.docx"'
        assert response.content == b"Test file content"
```

### Критерии для ручного тестирования

1. **Тестирование экспорта в DOCX**
   - Экспортируйте транскрипцию с несколькими спикерами
   - Проверьте корректность форматирования спикеров (цвета, стили)
   - Убедитесь, что тайм-коды отображаются правильно
   - Проверьте читаемость документа в Microsoft Word и других редакторах

2. **Тестирование экспорта в SRT**
   - Экспортируйте транскрипцию в формат SRT
   - Проверьте корректность временных меток
   - Загрузите SRT-файл в видеоплеер и убедитесь, что субтитры отображаются правильно
   - Проверьте корректность отображения спикеров

3. **Тестирование экспорта в JSON**
   - Экспортируйте транскрипцию в формат JSON
   - Проверьте наличие всех метаданных и сегментов
   - Убедитесь, что JSON валиден и может быть прочитан другими программами
   - Проверьте корректность кодировки русского текста

4. **Тестирование экспорта в текстовый формат**
   - Экспортируйте транскрипцию в текстовый формат
   - Проверьте читаемость и структуру текста
   - Убедитесь, что тайм-коды и спикеры отображаются корректно
   - Проверьте возможность копирования текста в другие приложения

5. **Тестирование API для скачивания**
   - Отправьте запрос на экспорт через API
   - Получите ссылки на скачивание и проверьте их работоспособность
   - Убедитесь, что файлы скачиваются с правильными именами и типами MIME
   - Проверьте обработку ошибок при запросе несуществующих файлов

6. **Тестирование интеграции с ботом**
   - Запустите транскрипцию через бота
   - Проверьте отображение кнопок экспорта после завершения транскрипции
   - Скачайте файлы в разных форматах и проверьте их содержимое
   - Убедитесь, что ссылки на скачивание работают корректно

7. **Тестирование производительности**
   - Экспортируйте большую транскрипцию (>30 минут)
   - Измерьте время экспорта для разных форматов
   - Проверьте использование памяти при экспорте больших файлов
   - Убедитесь, что система корректно обрабатывает параллельные запросы на экспорт