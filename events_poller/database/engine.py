from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

import asyncpg

from events_poller.logger import logger
from events_poller.settings import DatabaseConfig


class DatabaseError(Exception): ...


class Database:
    def __init__(self, db_config: DatabaseConfig) -> None:
        self._db_config = db_config
        self._engine = self._create_engine()
        self._session = async_sessionmaker(self._engine)

    def _create_engine(self) -> AsyncEngine:
        try:
            return create_async_engine(
                "postgresql+asyncpg://",
                async_creator=self._get_connection,
                **self._db_config.pool_config.model_dump(),
            )
        except Exception as e:
            logger.exception("database.error", error=str(e))
            raise DatabaseError()

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
        self, commit: bool = False
    ) -> AsyncGenerator[AsyncSession, None]:
        async with self._session() as session:
            try:
                yield session
                if commit:
                    await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def close_connection(self) -> None:
        await self._engine.dispose()
        logger.info("All connections closed successfuly.")
