from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from events_poller.controllers.metrics import MetricsControllerDependency
from events_poller.models.models import (
    EventAvgTimeMetricRequest,
    EventAvgTimeMetricResponse,
)


router = APIRouter()


@router.get("/event-avg-time/", response_model=EventAvgTimeMetricResponse)
async def get_event_avg_time(
    params: Annotated[EventAvgTimeMetricRequest, Depends()],
    controller: MetricsControllerDependency,
) -> EventAvgTimeMetricResponse | JSONResponse:
    return await controller.calculate_event_avg_time(params)
