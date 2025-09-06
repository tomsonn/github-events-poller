from datetime import datetime
from pydantic import AnyHttpUrl, BaseModel, ConfigDict

from events_poller.models.enum import EventTypeEnum


class EventModel(BaseModel):
    event_id: int
    event_type: EventTypeEnum
    actor_id: int
    repository_id: int
    repository_name: str
    created_at: datetime
    action: str

    model_config = ConfigDict(use_enum_values=True)


class ResponseMetaModel(BaseModel):
    data: list[EventModel]
    sleep: int
    rate_limited: bool = False
    pagination_link: AnyHttpUrl | None = None
