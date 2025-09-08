from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import MagicMock
import pytest_asyncio

from events_poller.controllers.database import DatabaseController
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
            await transaction.start()
            mock_db = MagicMock(Database)
            mock_db.get_session = patch_get_session
            yield mock_db
        finally:
            await transaction.rollback()


@pytest_asyncio.fixture
def database_controller(database: Database) -> DatabaseController:
    return DatabaseController(database)
