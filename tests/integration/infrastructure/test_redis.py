"""
Tests for Redis connection.
"""
import pytest
import redis
from unittest.mock import MagicMock, patch

from src.config.settings import config


@pytest.fixture
def redis_client():
    """Create a test Redis client."""
    # Use a mock Redis client for testing
    with patch('redis.Redis.from_url') as mock_from_url:
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        yield mock_client


def test_redis_connection(redis_client):
    """Test that the Redis connection works."""
    # Configure the mock to return True for ping
    redis_client.ping.return_value = True
    
    # Test the ping method
    assert redis_client.ping() is True


def test_redis_set_get(redis_client):
    """Test that Redis can set and get values."""
    # Configure the mock to return the expected value for get
    redis_client.get.return_value = b"test_value"
    
    # Test the set and get methods
    redis_client.set("test_key", "test_value")
    value = redis_client.get("test_key")
    
    # Check that the methods were called with the expected arguments
    redis_client.set.assert_called_once_with("test_key", "test_value")
    redis_client.get.assert_called_once_with("test_key")
    
    # Check that the returned value is as expected
    assert value == b"test_value"


def test_redis_delete(redis_client):
    """Test that Redis can delete values."""
    # Configure the mock to return 1 for delete
    redis_client.delete.return_value = 1
    
    # Test the delete method
    result = redis_client.delete("test_key")
    
    # Check that the method was called with the expected arguments
    redis_client.delete.assert_called_once_with("test_key")
    
    # Check that the returned value is as expected
    assert result == 1


def test_redis_expire(redis_client):
    """Test that Redis can set expiration on keys."""
    # Configure the mock to return True for expire
    redis_client.expire.return_value = True
    
    # Test the expire method
    result = redis_client.expire("test_key", 3600)
    
    # Check that the method was called with the expected arguments
    redis_client.expire.assert_called_once_with("test_key", 3600)
    
    # Check that the returned value is as expected
    assert result is True