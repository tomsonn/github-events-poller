from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from events_poller.controllers.metrics import MetricsControllerDependency
from events_poller.models.models import (
    EventAvgTimeMetricRequest,
    EventAvgTimeMetricResponse,
    RepositoriesWithMultipleEventsRequest,
    RepositoriesWithMultipleEventsResponse,
    TotalEventsMetricRequest,
    TotalEventsMetricResponse,
)


router = APIRouter()


@router.get("/event-avg-time", response_model=EventAvgTimeMetricResponse)
async def get_event_avg_time(
    params: Annotated[EventAvgTimeMetricRequest, Depends()],
    controller: MetricsControllerDependency,
) -> EventAvgTimeMetricResponse | JSONResponse:
    return await controller.calculate_event_avg_time(params)


@router.get("/events-total-count", response_model=TotalEventsMetricResponse)
async def get_events_total_count(
    params: Annotated[TotalEventsMetricRequest, Depends()],
    controller: MetricsControllerDependency,
) -> TotalEventsMetricResponse | JSONResponse:
    return await controller.get_events_total_count(params)


@router.get(
    "/multiple-events-repos", response_model=RepositoriesWithMultipleEventsResponse
)
async def get_repositories_with_multiple_events(
    params: Annotated[RepositoriesWithMultipleEventsRequest, Depends()],
    controller: MetricsControllerDependency,
) -> RepositoriesWithMultipleEventsResponse:
    return await controller.get_repositories_with_multiple_events(params)
