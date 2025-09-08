import pytest

from datetime import datetime, timezone

from events_poller.controllers.database import DatabaseController
from events_poller.models.enum import EventTypeEnum
from events_poller.models.models import EventModel
from tests.mock_data import EVENTS_BULK


@pytest.mark.asyncio
async def test_insert_data(database_controller: DatabaseController) -> None:
    event_in = EventModel(
        event_id=123,
        event_type=EventTypeEnum.PR_EVENT,
        actor_id=111,
        repository_id=666,
        repository_name="my-repository",
        created_at=datetime.now(tz=timezone.utc),
        action="opened",
    )
    await database_controller.insert_data(event_in)
    event_db_orm = await database_controller.get_events_by_type(
        event_type=EventTypeEnum.PR_EVENT
    )
    assert event_db_orm
    assert len(event_db_orm) == 1

    event_db = EventModel.model_validate(event_db_orm[0])
    assert event_in == event_db


@pytest.mark.asyncio
async def test_insert_data_bulk(database_controller: DatabaseController) -> None:
    events_in = EVENTS_BULK[:3]
    events_in_count = await database_controller.insert_data_bulk(events_in)
    assert len(events_in) == events_in_count

    events_db_orm = await database_controller.get_events_by_type(
        event_type=EventTypeEnum.PR_EVENT
    )
    events_db = [EventModel.model_validate(e) for e in events_db_orm]
    for e_in, e_db in zip(events_in, events_db):
        assert e_in == e_db


@pytest.mark.parametrize(
    "event_type, repository_name, action, count",
    [
        (EventTypeEnum.PR_EVENT, None, "opened", 2),
        (EventTypeEnum.ISSUES_EVENT, "my-repository-1", "opened", 1),
        (EventTypeEnum.WATCH_EVENT, "my-repository-1", None, 2),
        (EventTypeEnum.PR_EVENT, None, None, 3),
    ],
)
@pytest.mark.asyncio
async def test_get_events_by_type(
    event_type: EventTypeEnum,
    repository_name: str | None,
    action: str | None,
    count: int,
    database_controller: DatabaseController,
) -> None:
    _ = await database_controller.insert_data_bulk(EVENTS_BULK)
    events_db_orm = await database_controller.get_events_by_type(
        event_type=event_type, repository_name=repository_name, action=action
    )
    assert len(events_db_orm) == count


@pytest.mark.parametrize(
    "offset, events_grouped",
    [
        (20, [(EventTypeEnum.PR_EVENT, 2), (EventTypeEnum.WATCH_EVENT, 1)]),
        (
            3600,
            [
                (EventTypeEnum.ISSUES_EVENT, 1),
                (EventTypeEnum.PR_EVENT, 3),
                (EventTypeEnum.WATCH_EVENT, 2),
            ],
        ),
        (
            10000,
            [
                (EventTypeEnum.ISSUES_EVENT, 2),
                (EventTypeEnum.PR_EVENT, 3),
                (EventTypeEnum.WATCH_EVENT, 2),
            ],
        ),
    ],
)
@pytest.mark.asyncio
async def test_get_events_grouped_by_type(
    offset: int,
    events_grouped: list[tuple[EventTypeEnum, int]],
    database_controller: DatabaseController,
) -> None:
    _ = await database_controller.insert_data_bulk(EVENTS_BULK)
    events_db_orm = await database_controller.get_events_grouped_by_type(offset)
    assert len(events_db_orm) == len(events_grouped)
    for e_grouped in events_grouped:
        assert e_grouped in events_db_orm


@pytest.mark.parametrize("offset, event_id", [(20, 111), (3600, 114), (10000, 117)])
@pytest.mark.asyncio
async def test_get_oldest_event(
    offset: int, event_id: int, database_controller: DatabaseController
) -> None:
    _ = await database_controller.insert_data_bulk(EVENTS_BULK)
    event_db_orm = await database_controller.get_oldest_event(offset)
    assert (
        EventModel.model_validate(event_db_orm)
        == [e for e in EVENTS_BULK if e.event_id == event_id][0]
    )


@pytest.mark.parametrize(
    "event_type, minimal_events_count, repositories_grouped_by_event_type",
    [
        (EventTypeEnum.PR_EVENT, 2, [("my-repository", 3)]),
        (EventTypeEnum.WATCH_EVENT, 1, [("my-repository-1", 2)]),
        (EventTypeEnum.ISSUES_EVENT, 1, []),
    ],
)
@pytest.mark.asyncio
async def test_get_repositories_grouped_by_event_type(
    event_type: EventTypeEnum,
    minimal_events_count: int,
    repositories_grouped_by_event_type: list[tuple[str, int]],
    database_controller: DatabaseController,
) -> None:
    _ = await database_controller.insert_data_bulk(EVENTS_BULK)
    event_db_orm = await database_controller.get_repositories_grouped_by_event_type(
        event_type=event_type, minimal_events_count=minimal_events_count
    )
    assert len(event_db_orm) == len(repositories_grouped_by_event_type)
    for r in repositories_grouped_by_event_type:
        assert r in event_db_orm
