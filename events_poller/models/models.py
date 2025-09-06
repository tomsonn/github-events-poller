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


class GitHubApiResponseMetaModel(BaseModel):
    data: list[EventModel]
    sleep: int
    rate_limited: bool = False
    pagination_link: AnyHttpUrl | None = None


class MetricBaseRequest(BaseModel):
    repository_name: str | None = None
    action: str | None = None


class EventAvgTimeMetricRequest(MetricBaseRequest):
    event_type: EventTypeEnum = EventTypeEnum.PR_EVENT


class TotalEventsMetricRequest(MetricBaseRequest):
    offset: int
