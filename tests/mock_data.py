from datetime import datetime, timedelta, timezone
from events_poller.models.enum import EventTypeEnum
from events_poller.models.models import EventModel

DATETIME_NOW = datetime.now(timezone.utc)


EVENTS_BULK = [
    EventModel(
        event_id=111,
        event_type=EventTypeEnum.PR_EVENT,
        actor_id=111,
        repository_id=666,
        repository_name="my-repository",
        created_at=DATETIME_NOW - timedelta(seconds=10),
        action="opened",
    ),
    EventModel(
        event_id=112,
        event_type=EventTypeEnum.PR_EVENT,
        actor_id=111,
        repository_id=666,
        repository_name="my-repository",
        created_at=DATETIME_NOW - timedelta(seconds=8),
        action="opened",
    ),
    EventModel(
        event_id=113,
        event_type=EventTypeEnum.WATCH_EVENT,
        actor_id=111,
        repository_id=666,
        repository_name="my-repository-1",
        created_at=DATETIME_NOW - timedelta(seconds=6),
        action="closed",
    ),
    EventModel(
        event_id=114,
        event_type=EventTypeEnum.WATCH_EVENT,
        actor_id=111,
        repository_id=666,
        repository_name="my-repository-1",
        created_at=DATETIME_NOW - timedelta(minutes=55),
        action="opened",
    ),
    EventModel(
        event_id=115,
        event_type=EventTypeEnum.PR_EVENT,
        actor_id=111,
        repository_id=666,
        repository_name="my-repository",
        created_at=DATETIME_NOW - timedelta(minutes=50),
        action="closed",
    ),
    EventModel(
        event_id=116,
        event_type=EventTypeEnum.ISSUES_EVENT,
        actor_id=111,
        repository_id=666,
        repository_name="my-repository-1",
        created_at=DATETIME_NOW - timedelta(minutes=45),
        action="opened",
    ),
    EventModel(
        event_id=117,
        event_type=EventTypeEnum.ISSUES_EVENT,
        actor_id=111,
        repository_id=666,
        repository_name="my-repository-2",
        created_at=DATETIME_NOW - timedelta(hours=2),
        action="opened",
    ),
]
