from typing import Annotated

from fastapi import Depends, Request
from events_poller.database.models import Events
from events_poller.logger import logger
from events_poller.controllers.database import DatabaseController
from events_poller.models.models import (
    EventAvgTimeMetricRequest,
    EventAvgTimeMetricResponse,
)


class CalculationFailedError(Exception): ...


class MetricsController:
    def __init__(self, db_controller: DatabaseController) -> None:
        self._db_controller = db_controller

    @staticmethod
    def _calculate_avg_time(events: list[Events]) -> float:
        # Sum of the difference between two adjacent events
        total_time_diff = 0
        for idx in range(len(events) - 1):
            diff = (events[idx + 1].created_at - events[idx].created_at).total_seconds()
            logger.info(
                f"diff between event {events[idx + 1].event_id} and {events[idx].event_id}",
                diff=diff,
            )
            total_time_diff += diff

        avg_time = total_time_diff / (len(events) - 1)
        logger.info(
            "Calculated avg time between events",
            total_time_diff=total_time_diff,
            events_count=len(events),
            avg_time=avg_time,
        )
        return avg_time

    async def calculate_event_avg_time(
        self, params: EventAvgTimeMetricRequest
    ) -> EventAvgTimeMetricResponse | None:
        events = await self._db_controller.get_events_by_type(**params.model_dump())
        events_sorted = sorted(events, key=lambda x: x.created_at)

        if not events_sorted:
            logger.warning("No data to calculate metric", **params.model_dump())
            raise CalculationFailedError()

        return EventAvgTimeMetricResponse(
            oldest_event_time=events_sorted[0].created_at,
            repository_name=params.repository_name or "all",
            events_count=len(events_sorted),
            avg_time=round(self._calculate_avg_time(events_sorted), 2),
        )


def get_metrics_controller(request: Request) -> MetricsController:
    return request.app.state.controller


MetricsControllerDependency = Annotated[
    MetricsController, Depends(get_metrics_controller)
]
