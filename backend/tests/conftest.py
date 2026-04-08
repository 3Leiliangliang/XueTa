from __future__ import annotations

import sqlite3
import tempfile
import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from pgvector.sqlalchemy import Vector
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.main import app
from app.models import Base
from app.models.user import User, UserProfile, UserStatus
from app.services.llm import service as llm_service

TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

sqlite3.register_adapter(uuid.UUID, lambda value: str(value))


@compiles(JSONB, "sqlite")
def _compile_jsonb_for_sqlite(element, compiler, **kw):
    return "TEXT"


@compiles(ARRAY, "sqlite")
def _compile_array_for_sqlite(element, compiler, **kw):
    return "TEXT"


@compiles(PGUUID, "sqlite")
def _compile_uuid_for_sqlite(element, compiler, **kw):
    return "TEXT"


@compiles(Vector, "sqlite")
def _compile_vector_for_sqlite(element, compiler, **kw):
    return "TEXT"


@pytest.fixture
def session_factory(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "test")
    monkeypatch.setattr(settings, "run_migrations_on_startup", False)
    monkeypatch.setattr(settings, "auto_create_tables", False)
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "local_storage_path", tempfile.gettempdir())
    llm_service._get_openai_client.cache_clear()

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    try:
        yield SessionLocal
    finally:
        llm_service._get_openai_client.cache_clear()
        engine.dispose()


@pytest.fixture
def test_user(session_factory) -> User:
    with session_factory() as db:
        user = User(
            id=TEST_USER_ID,
            username="integration-user",
            email="integration@example.com",
            status=UserStatus.active,
            email_verified=True,
        )
        profile = UserProfile(user=user, display_name="Integration User")
        db.add_all([user, profile])
        db.commit()
        db.refresh(user)
        return user


@pytest.fixture
def client(session_factory, test_user) -> Iterator[TestClient]:
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    def override_get_current_user() -> User:
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
