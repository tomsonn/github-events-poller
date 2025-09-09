from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from events_poller.controllers.visualize import VisualizeControllerDependency
from events_poller.models.enum import GraphTypeEnum
from events_poller.models.models import (
    EventAvgTimeVisualizeRequest,
    TotalEventsMetricRequest,
)


router = APIRouter()


@router.get("/event-avg-time", response_class=HTMLResponse)
async def get_event_avg_time(
    params: Annotated[EventAvgTimeVisualizeRequest, Depends()],
    controller: VisualizeControllerDependency,
) -> HTMLResponse:
    fig = await controller.get_graph(params=params, graph_type=GraphTypeEnum.AVG_TIME)
    return HTMLResponse(fig.to_html(full_html=True, include_plotlyjs="cdn"))


@router.get("/events-total-count", response_class=HTMLResponse)
async def get_events_total_count(
    params: Annotated[TotalEventsMetricRequest, Depends()],
    controller: VisualizeControllerDependency,
) -> HTMLResponse:
    fig = await controller.get_graph(
        params=params, graph_type=GraphTypeEnum.TOTAL_COUNT
    )
    return HTMLResponse(fig.to_html(full_html=True, include_plotlyjs="cdn"))
