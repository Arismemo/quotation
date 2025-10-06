"""Test configuration and fixtures."""

import os
import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Create a temporary SQLite database for testing."""
    # Create a temporary file for the database
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)
    return f"sqlite:///{db_path}"


@pytest.fixture(scope="session")
def test_engine(test_db_url: str):
    """Create a test database engine."""
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def test_db_session(test_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_db_session) -> Generator[TestClient, None, None]:
    """Create a test client with database dependency override."""

    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "password": "testpassword123",
        "email": "test@example.com",
    }


@pytest.fixture
def test_image_data():
    """Sample image data for testing."""
    # This would be actual image bytes in a real test
    return b"fake_image_data"
