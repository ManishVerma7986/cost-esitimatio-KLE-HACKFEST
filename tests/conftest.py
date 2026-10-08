"""Pytest fixtures for testing Costimator platform."""

from __future__ import annotations

import uuid
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_current_user, get_db
from app.api.main import app as fastapi_app
from app.db.base import Base
import app.db.models  # noqa: F401
from app.db.models.user import User


@pytest.fixture(scope="session")
def test_engine():
    """Create in-memory SQLite engine for the test session."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Provide a clean transactional session for each test function."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        full_name="Test Architect",
        hashed_password="hashed_test_pass",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def client(db_session: Session, test_user: User) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with overridden DB and user dependencies."""
    def override_get_db():
        yield db_session

    def override_get_current_user():
        return test_user

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(fastapi_app) as test_client:
        yield test_client

    fastapi_app.dependency_overrides.clear()
