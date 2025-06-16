"""
Tests for database connection.
"""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database.models import Base


@pytest.fixture
def db_engine():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create a test database session."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_database_connection(db_session):
    """Test that the database connection works."""
    # Execute a simple query to check the connection
    result = db_session.execute(text("SELECT 1")).scalar()
    assert result == 1


def test_database_tables(db_engine):
    """Test that all expected tables are created."""
    inspector = db_engine.dialect.inspector
    tables = inspector.get_table_names()
    
    # Check that the expected tables exist
    expected_tables = [
        "audio_files",
        "transcriptions",
        "transcription_segments",
        "diarizations",
        "speaker_segments",
        "users",
        "user_settings"
    ]
    
    for table in expected_tables:
        assert table in tables, f"Table {table} not found in database"