import pytest
from events_poller.controllers.database import DatabaseController
from events_poller.controllers.metrics import CalculationFailedError, MetricsController
from events_poller.models.enum import EventTypeEnum
from events_poller.models.models import (
    EventAvgTimeMetricRequest,
    RepositoriesWithMultipleEventsRequest,
)
from tests.mock_data import EVENTS_BULK


@pytest.mark.asyncio
async def test_calculate_avg_time_no_data(
    metrics_controller: MetricsController,
) -> None:
    with pytest.raises(CalculationFailedError):
        # As there are < 2 events stored in the db, controller should raise CalculationFailedError exception
        await metrics_controller.calculate_event_avg_time(EventAvgTimeMetricRequest())


@pytest.mark.asyncio
async def test_calculate_avg_time(
    database_controller: DatabaseController, metrics_controller: MetricsController
) -> None:
    event_count_to_store = 3
    total_diff = 0
    event_avg_time_params = EventAvgTimeMetricRequest()
    events_in = [
        e for e in EVENTS_BULK if e.event_type == event_avg_time_params.event_type
    ][:event_count_to_store]

    # calculate time difference manually and compare it with the results from the controller
    events_in_sorted = sorted(events_in, key=lambda x: x.created_at, reverse=True)
    for idx in range(len(events_in_sorted) - 1):
        total_diff += (
            events_in_sorted[idx].created_at - events_in_sorted[idx + 1].created_at
        ).total_seconds()

    avg_time_calculated_manually = round(total_diff / (event_count_to_store - 1))

    _ = await database_controller.insert_data_bulk(events_in)
    events_avg_time = await metrics_controller.calculate_event_avg_time(
        event_avg_time_params
    )

    assert (
        events_avg_time.oldest_event_time
        == events_in[event_count_to_store - 1].created_at
    )
    assert events_avg_time.repository_name == "all"
    assert events_avg_time.events_count == event_count_to_store
    assert events_avg_time.avg_time == avg_time_calculated_manually


@pytest.mark.parametrize(
    "minimal_events_count, event_type, repositories_count",
    [
        (2, EventTypeEnum.PR_EVENT, 1),
        (3, EventTypeEnum.PR_EVENT, 0),
    ],
)
@pytest.mark.asyncio
async def test_get_repositories_with_multiple_events(
    minimal_events_count: int,
    event_type: EventTypeEnum,
    repositories_count: int,
    database_controller: DatabaseController,
    metrics_controller: MetricsController,
) -> None:
    repos_with_multi_events_params = RepositoriesWithMultipleEventsRequest(
        event_type=event_type, minimal_events_count=minimal_events_count
    )
    _ = await database_controller.insert_data_bulk(EVENTS_BULK)
    repos_db = await metrics_controller.get_repositories_with_multiple_events(
        repos_with_multi_events_params
    )
    assert len(repos_db.repositories.keys()) == repositories_count
