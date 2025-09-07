from typing import Annotated

from fastapi import Depends, Request
from events_poller.database.models import Events
from events_poller.logger import logger
from events_poller.controllers.database import DatabaseController
from events_poller.models.enum import EventTypeEnum
from events_poller.models.models import (
    EventAvgTimeMetricRequest,
    EventAvgTimeMetricResponse,
    GroupedEventsCountModel,
    RepositoriesWithMultipleEventsRequest,
    RepositoriesWithMultipleEventsResponse,
    TotalEventsMetricRequest,
    TotalEventsMetricResponse,
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

    @staticmethod
    def get_event_count_by_type(
        event_type: EventTypeEnum, events_grouped: list[tuple[EventTypeEnum, int]]
    ) -> int:
        event_by_type = [e for e in events_grouped if e[0] == event_type]
        return event_by_type[0][1] if event_by_type else 0

    async def get_events_total_count(
        self, params: TotalEventsMetricRequest
    ) -> TotalEventsMetricResponse:
        events_grouped = await self._db_controller.get_events_grouped_by_type(
            **params.model_dump()
        )

        # I'm awate, that this method doesn't have to return correct value in 100% of cases,
        # if poller is running
        oldest_event = await self._db_controller.get_oldest_event(params.offset)
        return TotalEventsMetricResponse(
            oldest_event_time=oldest_event.created_at,
            repository_name=params.repository_name or "all",
            events_count=GroupedEventsCountModel(
                pr_event=self.get_event_count_by_type(
                    EventTypeEnum.PR_EVENT, events_grouped
                ),
                watch_event=self.get_event_count_by_type(
                    EventTypeEnum.WATCH_EVENT, events_grouped
                ),
                issue_event=self.get_event_count_by_type(
                    EventTypeEnum.ISSUES_EVENT, events_grouped
                ),
                total=sum(e[1] for e in events_grouped),
            ),
        )

    async def get_repositories_with_multiple_events(
        self, params: RepositoriesWithMultipleEventsRequest
    ) -> RepositoriesWithMultipleEventsResponse:
        repositories_grouped = (
            await self._db_controller.get_repositories_grouped_by_event_type(
                **params.model_dump()
            )
        )
        return RepositoriesWithMultipleEventsResponse(
            event_type=params.event_type,
            repositories={r[0]: r[1] for r in repositories_grouped},
        )


def get_metrics_controller(request: Request) -> MetricsController:
    return request.app.state.controller


MetricsControllerDependency = Annotated[
    MetricsController, Depends(get_metrics_controller)
]
