"""
Tests for audio domain entities.
"""
import pytest
from pathlib import Path

from src.domains.audio.entities import AudioFile, AudioFormat


def test_audio_format_enum():
    """Test that AudioFormat enum has the expected values."""
    assert AudioFormat.MP3 == "mp3"
    assert AudioFormat.WAV == "wav"
    assert AudioFormat.OGG == "ogg"
    assert AudioFormat.M4A == "m4a"
    assert AudioFormat.WEBM == "webm"


def test_audio_file_creation():
    """Test that AudioFile can be created with the expected values."""
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


def test_audio_file_with_error():
    """Test that AudioFile can be created with an error message."""
    audio_file = AudioFile(
        id="123e4567-e89b-12d3-a456-426614174000",
        user_id=123456789,
        original_filename="test_audio.mp3",
        format=AudioFormat.MP3,
        size_bytes=1024000,
        is_valid=False,
        error_message="Invalid audio format"
    )
    
    assert audio_file.is_valid is False
    assert audio_file.error_message == "Invalid audio format"
    assert audio_file.duration_seconds is None
    assert audio_file.path is None
    assert audio_file.processed_path is None