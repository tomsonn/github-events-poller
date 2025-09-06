from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

import asyncpg

from events_poller.settings import DatabaseConfig


class Database:
    def __init__(self, db_config: DatabaseConfig) -> None:
        self._db_config = db_config
        self._engine = self._create_engine()
        self._session = async_sessionmaker(self._engine)

    def _create_engine(self) -> AsyncEngine:
        return create_async_engine(
            "postgresql+asyncpg://",
            async_creator=self._get_connection,
            **self._db_config.pool_config.model_dump(),
        )

    async def _get_connection(self) -> asyncpg.Connection:
        return await asyncpg.connect(
            host=self._db_config.host,
            port=self._db_config.port,
            user=self._db_config.user,
            password=self._db_config.password,
            database=self._db_config.database,
        )

    @asynccontextmanager
    async def get_session(
        self, commit: bool = True
    ) -> AsyncGenerator[AsyncSession, None]:
        async with self._session() as session:
            try:
                yield session
                if commit:
                    await session.commit()
            except Exception:
                await session.rollback()
                raise
