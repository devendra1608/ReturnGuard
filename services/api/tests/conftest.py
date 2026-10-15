import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.db import get_session
from app.main import app
from app.models import Base


@pytest.fixture
def client(tmp_path):
    database_path = tmp_path / "returnguard_test.db"

    test_engine = create_async_engine(
        f"sqlite+aiosqlite:///{database_path.as_posix()}",
        poolclass=NullPool,
    )

    test_session_factory = async_sessionmaker(
        test_engine,
        expire_on_commit=False,
    )

    async def setup_database():
        async with test_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def cleanup_database():
        await test_engine.dispose()

    asyncio.run(setup_database())

    async def override_get_session():
        async with test_session_factory() as session:
            yield session

    # Preserve any dependency overrides installed by other tests.
    previous_overrides = app.dependency_overrides.copy()
    previous_factory = getattr(
        app.state, "test_session_factory", None
    )

    app.dependency_overrides[get_session] = override_get_session
    app.state.test_session_factory = test_session_factory

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)

        if previous_factory is None:
            if hasattr(app.state, "test_session_factory"):
                del app.state.test_session_factory
        else:
            app.state.test_session_factory = previous_factory

        asyncio.run(cleanup_database())
