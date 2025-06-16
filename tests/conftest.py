"""
Shared pytest fixtures for all tests.
"""
import pytest


@pytest.fixture
def sample_user_id():
    """Return a sample user ID for testing."""
    return 123456789


@pytest.fixture
def sample_file_id():
    """Return a sample file ID for testing."""
    return "123e4567-e89b-12d3-a456-426614174000"