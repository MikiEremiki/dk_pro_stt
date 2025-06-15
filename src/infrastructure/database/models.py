from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class AudioFile(Base):
    __tablename__ = "audio_files"

    id = Column(String, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    original_filename = Column(String(255), nullable=False)
    format = Column(String(10), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    duration_seconds = Column(Float, nullable=True)
    path = Column(String(255), nullable=True)
    processed_path = Column(String(255), nullable=True)
    is_valid = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transcriptions = relationship("Transcription", back_populates="audio_file", cascade="all, delete-orphan")
    diarizations = relationship("Diarization", back_populates="audio_file", cascade="all, delete-orphan")


class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(String, primary_key=True)
    audio_file_id = Column(String, ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    model = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    language = Column(String(10), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    audio_file = relationship("AudioFile", back_populates="transcriptions")
    segments = relationship("TranscriptionSegment", back_populates="transcription", cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="transcription", cascade="all, delete-orphan")


class TranscriptionSegment(Base):
    __tablename__ = "transcription_segments"

    id = Column(String, primary_key=True)
    transcription_id = Column(String, ForeignKey("transcriptions.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    transcription = relationship("Transcription", back_populates="segments")


class Diarization(Base):
    __tablename__ = "diarizations"

    id = Column(String, primary_key=True)
    audio_file_id = Column(String, ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    status = Column(String(20), nullable=False)
    num_speakers = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    audio_file = relationship("AudioFile", back_populates="diarizations")
    segments = relationship("SpeakerSegment", back_populates="diarization", cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="diarization", cascade="all, delete-orphan")


class SpeakerSegment(Base):
    __tablename__ = "speaker_segments"

    id = Column(String, primary_key=True)
    diarization_id = Column(String, ForeignKey("diarizations.id", ondelete="CASCADE"), nullable=False)
    speaker_id = Column(Integer, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    diarization = relationship("Diarization", back_populates="segments")


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    language_code = Column(String(10), nullable=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="user", cascade="all, delete-orphan")


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    preferred_model = Column(String(50), nullable=False, default="whisper-large-v3")
    preferred_export_format = Column(String(20), nullable=False, default="docx")
    auto_detect_language = Column(Boolean, default=True)
    auto_delete_files = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="settings")


class Export(Base):
    __tablename__ = "exports"

    id = Column(String, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    transcription_id = Column(String, ForeignKey("transcriptions.id", ondelete="SET NULL"), nullable=True)
    diarization_id = Column(String, ForeignKey("diarizations.id", ondelete="SET NULL"), nullable=True)
    format = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    file_path = Column(String(255), nullable=True)
    file_url = Column(String(255), nullable=True)
    options = Column(Text, nullable=True)  # JSON serialized options
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="exports")
    transcription = relationship("Transcription", back_populates="exports")
    diarization = relationship("Diarization", back_populates="exports")