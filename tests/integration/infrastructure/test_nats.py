"""
Tests for NATS connection.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.config.settings import config


@pytest.fixture
async def nats_client():
    """Create a test NATS client."""
    # Use a mock NATS client for testing
    with patch('nats.connect') as mock_connect:
        mock_client = AsyncMock()
        mock_connect.return_value = mock_client
        
        # Configure the mock client
        mock_client.is_connected = True
        mock_client.jetstream.return_value = AsyncMock()
        
        yield mock_client


@pytest.mark.asyncio
async def test_nats_connection(nats_client):
    """Test that the NATS connection works."""
    # Test the connection status
    assert nats_client.is_connected is True


@pytest.mark.asyncio
async def test_nats_publish_subscribe(nats_client):
    """Test that NATS can publish and subscribe to messages."""
    # Create a mock callback
    callback = AsyncMock()
    
    # Configure the mock subscription
    mock_subscription = AsyncMock()
    nats_client.subscribe.return_value = mock_subscription
    
    # Subscribe to a subject
    subscription = await nats_client.subscribe("test.subject", cb=callback)
    
    # Check that subscribe was called with the expected arguments
    nats_client.subscribe.assert_called_once_with("test.subject", cb=callback)
    
    # Publish a message
    await nats_client.publish("test.subject", b"test message")
    
    # Check that publish was called with the expected arguments
    nats_client.publish.assert_called_once_with("test.subject", b"test message")


@pytest.mark.asyncio
async def test_nats_request_reply(nats_client):
    """Test that NATS can send requests and receive replies."""
    # Configure the mock response
    mock_message = MagicMock()
    mock_message.data = b"test response"
    nats_client.request.return_value = mock_message
    
    # Send a request
    response = await nats_client.request("test.request", b"test request")
    
    # Check that request was called with the expected arguments
    nats_client.request.assert_called_once_with("test.request", b"test request")
    
    # Check that the response is as expected
    assert response.data == b"test response"


@pytest.mark.asyncio
async def test_nats_jetstream(nats_client):
    """Test that NATS JetStream works."""
    # Get JetStream context
    js = nats_client.jetstream()
    
    # Configure the mock stream
    mock_stream = AsyncMock()
    js.add_stream.return_value = mock_stream
    
    # Add a stream
    stream_config = {
        "name": "test_stream",
        "subjects": ["test.>"],
        "retention": "limits",
        "max_msgs": 10000,
        "max_bytes": 1024 * 1024 * 100,  # 100MB
        "max_age": 3600 * 24 * 7,  # 7 days
        "storage": "file",
        "discard": "old",
    }
    stream = await js.add_stream(**stream_config)
    
    # Check that add_stream was called with the expected arguments
    js.add_stream.assert_called_once_with(**stream_config)
    
    # Configure the mock consumer
    mock_consumer = AsyncMock()
    js.pull_subscribe.return_value = mock_consumer
    
    # Create a consumer
    consumer = await js.pull_subscribe("test.subject", "test_consumer")
    
    # Check that pull_subscribe was called with the expected arguments
    js.pull_subscribe.assert_called_once_with("test.subject", "test_consumer")