from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import MagicMock
import pytest_asyncio

from events_poller.api.app import app
from events_poller.controllers.database import DatabaseController
from events_poller.controllers.metrics import MetricsController, get_metrics_controller
from events_poller.database.engine import Database
from events_poller.settings import DatabaseConfig


@pytest_asyncio.fixture(scope="session")
def database_config() -> DatabaseConfig:
    db_config = DatabaseConfig()
    db_config.database = db_config.database + "_test"
    return db_config


@pytest_asyncio.fixture
async def session(database_config: DatabaseConfig) -> AsyncGenerator[AsyncSession]:
    db = Database(database_config)
    async with db.get_session() as session:
        yield session

    await db.close_connection()


@pytest_asyncio.fixture
async def database(session: AsyncSession) -> AsyncGenerator[Database]:
    @asynccontextmanager
    async def patch_get_session(commit: bool = False) -> AsyncGenerator[AsyncSession]:
        yield session

    async with session.begin_nested() as transaction:
        try:
            mock_db = MagicMock(spec=Database)
            mock_db.get_session = patch_get_session
            yield mock_db
        finally:
            await transaction.rollback()


@pytest.fixture
def database_controller(database: Database) -> DatabaseController:
    return DatabaseController(database)


@pytest.fixture
def metrics_controller(database_controller: DatabaseController) -> MetricsController:
    return MetricsController(database_controller)


@pytest_asyncio.fixture
async def api_client(
    metrics_controller: MetricsController,
) -> AsyncGenerator[AsyncClient]:
    def get_mock_metrics_controller() -> MetricsController:
        return metrics_controller

    app.dependency_overrides[get_metrics_controller] = get_mock_metrics_controller

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testurl"
    ) as client:
        yield client
        app.dependency_overrides.clear()
