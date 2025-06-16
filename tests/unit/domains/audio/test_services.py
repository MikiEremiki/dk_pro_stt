"""
Tests for audio domain services.
"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from src.domains.audio.services import AudioService
from src.domains.audio.entities import AudioFile, AudioFormat


class TestAudioService:
    """Test cases for the AudioService interface."""

    def test_audio_service_interface(self):
        """Test that AudioService defines the expected methods."""
        # Check that the AudioService class has the expected methods
        assert hasattr(AudioService, 'validate_audio')
        assert hasattr(AudioService, 'convert_to_wav')
        assert hasattr(AudioService, 'get_audio_duration')
        assert hasattr(AudioService, 'normalize_volume')
        assert hasattr(AudioService, 'detect_silence')

    async def test_validate_audio_method(self, sample_user_id):
        """Test the validate_audio method of AudioService."""
        # Create a mock implementation of AudioService
        class MockAudioService(AudioService):
            async def validate_audio(self, file, filename, user_id):
                return AudioFile(
                    id="123e4567-e89b-12d3-a456-426614174000",
                    user_id=user_id,
                    original_filename=filename,
                    format=AudioFormat.MP3,
                    size_bytes=1024000,
                    is_valid=True
                )
            
            async def convert_to_wav(self, audio_file):
                pass
            
            async def get_audio_duration(self, file_path):
                pass
            
            async def normalize_volume(self, file_path):
                pass
            
            async def detect_silence(self, file_path):
                pass
        
        # Create a mock service
        service = MockAudioService()
        
        # Create a mock file
        mock_file = MagicMock()
        
        # Test the validate_audio method
        audio_file = await service.validate_audio(mock_file, "test_audio.mp3", sample_user_id)
        assert audio_file is not None
        assert audio_file.user_id == sample_user_id
        assert audio_file.original_filename == "test_audio.mp3"
        assert audio_file.format == AudioFormat.MP3
        assert audio_file.is_valid is True

    async def test_convert_to_wav_method(self, sample_user_id, sample_file_id):
        """Test the convert_to_wav method of AudioService."""
        # Create a mock implementation of AudioService
        class MockAudioService(AudioService):
            async def validate_audio(self, file, filename, user_id):
                pass
            
            async def convert_to_wav(self, audio_file):
                return Path(f"/tmp/audio/{audio_file.id}.wav")
            
            async def get_audio_duration(self, file_path):
                pass
            
            async def normalize_volume(self, file_path):
                pass
            
            async def detect_silence(self, file_path):
                pass
        
        # Create a mock service
        service = MockAudioService()
        
        # Create a test audio file
        audio_file = AudioFile(
            id=sample_file_id,
            user_id=sample_user_id,
            original_filename="test_audio.mp3",
            format=AudioFormat.MP3,
            size_bytes=1024000,
            path=Path(f"/tmp/audio/{sample_file_id}.mp3"),
            is_valid=True
        )
        
        # Test the convert_to_wav method
        wav_path = await service.convert_to_wav(audio_file)
        assert wav_path is not None
        assert wav_path == Path(f"/tmp/audio/{sample_file_id}.wav")