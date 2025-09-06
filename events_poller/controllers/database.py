from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy.sql.expression import func, select
from sqlalchemy.dialects.postgresql import insert
from events_poller.database.engine import Database
from events_poller.database.models import Events
from events_poller.logger import logger
from events_poller.models.enum import EventTypeEnum
from events_poller.models.models import EventModel


class DatabaseController:
    def __init__(self, database: Database) -> None:
        self._database = database

    async def insert_data(self, data: EventModel) -> None:
        statement = insert(Events).values(data.model_dump())
        statement = statement.on_conflict_do_nothing(index_elements=["event_id"])
        async with self._database.get_session(commit=True) as session:
            await session.execute(statement)
            logger.info("database_controller.insert_data.successful")

    async def insert_data_bulk(self, data_bulk: list[EventModel]) -> int:
        statement = insert(Events).values([data.model_dump() for data in data_bulk])
        statement = statement.on_conflict_do_nothing(
            index_elements=[Events.event_id]
        ).returning(Events.event_id)
        async with self._database.get_session(commit=True) as session:
            ret = await session.execute(statement)
            logger.info("database_controller.insert_data_bulk.successful")

        return len(ret.fetchall())

    async def get_events_by_type(
        self,
        event_type: EventTypeEnum,
        repository_name: str | None = None,
        action: Literal["opened", "closed"] | None = None,
    ) -> Sequence[Events]:
        filters = [Events.event_type == event_type]
        if repository_name:
            filters.append(Events.repository_name == repository_name.lower())
        if action:
            filters.append(Events.action == action)

        statement = select(Events).where(*filters)
        async with self._database.get_session(commit=False) as session:
            data = (await session.execute(statement)).scalars().all()
            logger.info(
                "database_controller.get_events_by_type.successful",
                data_count=len(data),
                event_type=event_type,
                repository_name=repository_name,
                action=action,
            )

        return data

    async def get_events_grouped_by_type(
        self,
        offset: int,
        repository_name: str | None = None,
        action: Literal["opened", "closed"] | None = None,
    ):
        filters = [Events.created_at >= datetime.now() - timedelta(seconds=offset)]
        if repository_name:
            filters.append(Events.repository_name == repository_name.lower())
        if action:
            filters.append(Events.action == action)

        statement = (
            select(Events.event_type, func.count())
            .where(*filters)
            .group_by(Events.event_type)
        )
        async with self._database.get_session() as session:
            res = (await session.execute(statement)).all()
            logger.info(
                "database_controller.get_events_grouped_by_type.successful",
                grouped_events=res,
                repository_name=repository_name,
                offset=offset,
                action=action,
            )

        return res
