import httpx
import pytest

from events_poller.controllers.database import DatabaseController
from events_poller.models.enum import EventTypeEnum
from events_poller.models.models import (
    EventAvgTimeMetricRequest,
    RepositoriesWithMultipleEventsRequest,
    TotalEventsMetricRequest,
)
from tests.mock_data import EVENTS_BULK


@pytest.mark.asyncio
async def test_get_avg_event_time(
    api_client: httpx.AsyncClient, database_controller: DatabaseController
) -> None:
    params = EventAvgTimeMetricRequest(event_type=EventTypeEnum.PR_EVENT)
    _ = await database_controller.insert_data_bulk(EVENTS_BULK)
    response = await api_client.get(
        "/metrics/event-avg-time", params=params.model_dump(exclude_none=True)
    )

    assert response.status_code == httpx.codes.OK


@pytest.mark.asyncio
async def test_get_avg_event_time_no_repository(api_client: httpx.AsyncClient) -> None:
    params = EventAvgTimeMetricRequest(event_type=EventTypeEnum.PR_EVENT)
    response = await api_client.get(
        "/metrics/event-avg-time", params=params.model_dump(exclude_none=True)
    )

    assert response.status_code == httpx.codes.BAD_REQUEST


@pytest.mark.asyncio
async def test_get_events_total_count(
    api_client: httpx.AsyncClient, database_controller: DatabaseController
) -> None:
    params = TotalEventsMetricRequest(offset=100)
    _ = await database_controller.insert_data_bulk(EVENTS_BULK)
    response = await api_client.get(
        "/metrics/events-total-count", params=params.model_dump(exclude_none=True)
    )

    assert response.status_code == httpx.codes.OK


@pytest.mark.asyncio
async def test_get_repositories_with_multiple_events(
    api_client: httpx.AsyncClient, database_controller: DatabaseController
) -> None:
    params = RepositoriesWithMultipleEventsRequest(event_type=EventTypeEnum.PR_EVENT)
    _ = await database_controller.insert_data_bulk(EVENTS_BULK)
    response = await api_client.get(
        "/metrics/multiple-events-repos", params=params.model_dump(exclude_none=True)
    )

    assert response.status_code == httpx.codes.OK
