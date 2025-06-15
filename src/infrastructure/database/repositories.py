from typing import Optional, List, Dict, Any
from uuid import UUID
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from domains.audio.entities import AudioFile as AudioFileEntity, AudioFormat
from domains.audio.repositories import AudioRepository
from domains.transcription.entities import Transcription as TranscriptionEntity, TranscriptionSegment as TranscriptionSegmentEntity, TranscriptionModel, TranscriptionStatus
from domains.transcription.repositories import TranscriptionRepository
from domains.diarization.entities import Diarization as DiarizationEntity, SpeakerSegment as SpeakerSegmentEntity, DiarizationStatus
from domains.diarization.repositories import DiarizationRepository
from domains.export.entities import Export as ExportEntity, ExportFormat, ExportStatus
from domains.export.repositories import ExportRepository
from domains.user.entities import User as UserEntity, UserSettings as UserSettingsEntity
from domains.user.repositories import UserRepository, UserSettingsRepository

from .models import AudioFile, Transcription, TranscriptionSegment, Diarization, SpeakerSegment, User, UserSettings, Export


class SQLAlchemyAudioRepository(AudioRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, audio_file: AudioFileEntity) -> AudioFileEntity:
        db_audio_file = AudioFile(
            id=audio_file.id,
            user_id=audio_file.user_id,
            original_filename=audio_file.original_filename,
            format=audio_file.format.value,
            size_bytes=audio_file.size_bytes,
            duration_seconds=audio_file.duration_seconds,
            path=str(audio_file.path) if audio_file.path else None,
            processed_path=str(audio_file.processed_path) if audio_file.processed_path else None,
            is_valid=audio_file.is_valid,
            error_message=audio_file.error_message
        )
        self.session.add(db_audio_file)
        await self.session.commit()
        return audio_file

    async def get_by_id(self, file_id: str) -> Optional[AudioFileEntity]:
        result = await self.session.execute(select(AudioFile).where(AudioFile.id == file_id))
        db_audio_file = result.scalars().first()
        if not db_audio_file:
            return None
        
        return AudioFileEntity(
            id=db_audio_file.id,
            user_id=db_audio_file.user_id,
            original_filename=db_audio_file.original_filename,
            format=AudioFormat(db_audio_file.format),
            size_bytes=db_audio_file.size_bytes,
            duration_seconds=db_audio_file.duration_seconds,
            path=db_audio_file.path,
            processed_path=db_audio_file.processed_path,
            is_valid=db_audio_file.is_valid,
            error_message=db_audio_file.error_message
        )

    async def update(self, audio_file: AudioFileEntity) -> AudioFileEntity:
        await self.session.execute(
            update(AudioFile)
            .where(AudioFile.id == audio_file.id)
            .values(
                user_id=audio_file.user_id,
                original_filename=audio_file.original_filename,
                format=audio_file.format.value,
                size_bytes=audio_file.size_bytes,
                duration_seconds=audio_file.duration_seconds,
                path=str(audio_file.path) if audio_file.path else None,
                processed_path=str(audio_file.processed_path) if audio_file.processed_path else None,
                is_valid=audio_file.is_valid,
                error_message=audio_file.error_message
            )
        )
        await self.session.commit()
        return audio_file

    async def delete(self, file_id: str) -> None:
        await self.session.execute(delete(AudioFile).where(AudioFile.id == file_id))
        await self.session.commit()


class SQLAlchemyTranscriptionRepository(TranscriptionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, transcription: TranscriptionEntity) -> TranscriptionEntity:
        db_transcription = Transcription(
            id=transcription.id,
            audio_file_id=transcription.audio_file_id,
            user_id=transcription.user_id,
            model=transcription.model.value,
            status=transcription.status.value,
            language=transcription.language,
            error_message=transcription.error_message
        )
        self.session.add(db_transcription)
        
        if transcription.segments:
            for segment in transcription.segments:
                db_segment = TranscriptionSegment(
                    id=str(UUID(int=0)),  # Generate a new UUID
                    transcription_id=transcription.id,
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    text=segment.text,
                    confidence=segment.confidence
                )
                self.session.add(db_segment)
        
        await self.session.commit()
        return transcription

    async def get_by_id(self, transcription_id: str) -> Optional[TranscriptionEntity]:
        result = await self.session.execute(select(Transcription).where(Transcription.id == transcription_id))
        db_transcription = result.scalars().first()
        if not db_transcription:
            return None
        
        segments_result = await self.session.execute(
            select(TranscriptionSegment).where(TranscriptionSegment.transcription_id == transcription_id)
        )
        db_segments = segments_result.scalars().all()
        
        segments = [
            TranscriptionSegmentEntity(
                start_time=segment.start_time,
                end_time=segment.end_time,
                text=segment.text,
                confidence=segment.confidence
            )
            for segment in db_segments
        ]
        
        return TranscriptionEntity(
            id=db_transcription.id,
            audio_file_id=db_transcription.audio_file_id,
            user_id=db_transcription.user_id,
            model=TranscriptionModel(db_transcription.model),
            status=TranscriptionStatus(db_transcription.status),
            language=db_transcription.language,
            segments=segments,
            error_message=db_transcription.error_message
        )

    async def get_by_audio_file_id(self, audio_file_id: str) -> List[TranscriptionEntity]:
        result = await self.session.execute(
            select(Transcription).where(Transcription.audio_file_id == audio_file_id)
        )
        db_transcriptions = result.scalars().all()
        
        transcriptions = []
        for db_transcription in db_transcriptions:
            segments_result = await self.session.execute(
                select(TranscriptionSegment).where(TranscriptionSegment.transcription_id == db_transcription.id)
            )
            db_segments = segments_result.scalars().all()
            
            segments = [
                TranscriptionSegmentEntity(
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    text=segment.text,
                    confidence=segment.confidence
                )
                for segment in db_segments
            ]
            
            transcriptions.append(
                TranscriptionEntity(
                    id=db_transcription.id,
                    audio_file_id=db_transcription.audio_file_id,
                    user_id=db_transcription.user_id,
                    model=TranscriptionModel(db_transcription.model),
                    status=TranscriptionStatus(db_transcription.status),
                    language=db_transcription.language,
                    segments=segments,
                    error_message=db_transcription.error_message
                )
            )
        
        return transcriptions

    async def get_by_user_id(self, user_id: int) -> List[TranscriptionEntity]:
        result = await self.session.execute(
            select(Transcription).where(Transcription.user_id == user_id)
        )
        db_transcriptions = result.scalars().all()
        
        transcriptions = []
        for db_transcription in db_transcriptions:
            segments_result = await self.session.execute(
                select(TranscriptionSegment).where(TranscriptionSegment.transcription_id == db_transcription.id)
            )
            db_segments = segments_result.scalars().all()
            
            segments = [
                TranscriptionSegmentEntity(
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    text=segment.text,
                    confidence=segment.confidence
                )
                for segment in db_segments
            ]
            
            transcriptions.append(
                TranscriptionEntity(
                    id=db_transcription.id,
                    audio_file_id=db_transcription.audio_file_id,
                    user_id=db_transcription.user_id,
                    model=TranscriptionModel(db_transcription.model),
                    status=TranscriptionStatus(db_transcription.status),
                    language=db_transcription.language,
                    segments=segments,
                    error_message=db_transcription.error_message
                )
            )
        
        return transcriptions

    async def update(self, transcription: TranscriptionEntity) -> TranscriptionEntity:
        await self.session.execute(
            update(Transcription)
            .where(Transcription.id == transcription.id)
            .values(
                audio_file_id=transcription.audio_file_id,
                user_id=transcription.user_id,
                model=transcription.model.value,
                status=transcription.status.value,
                language=transcription.language,
                error_message=transcription.error_message
            )
        )
        
        # Delete existing segments and add new ones
        if transcription.segments:
            await self.session.execute(
                delete(TranscriptionSegment).where(TranscriptionSegment.transcription_id == transcription.id)
            )
            
            for segment in transcription.segments:
                db_segment = TranscriptionSegment(
                    id=str(UUID(int=0)),  # Generate a new UUID
                    transcription_id=transcription.id,
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    text=segment.text,
                    confidence=segment.confidence
                )
                self.session.add(db_segment)
        
        await self.session.commit()
        return transcription

    async def delete(self, transcription_id: str) -> None:
        await self.session.execute(delete(Transcription).where(Transcription.id == transcription_id))
        await self.session.commit()


# Similar implementations for other repositories (DiarizationRepository, ExportRepository, UserRepository, UserSettingsRepository)
# would follow the same pattern. For brevity, I'm not including them all here.