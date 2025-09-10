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
    """
    Controller responsible for retrieving, processing, and calculating GitHub event metrics.

    This class acts as a service layer between the API endpoints and the database layer.
    It pulls event data from the database via the DatabaseController and computes metrics
    such as average time between events, total event counts, and repositories with a high
    number of specific events.

    Methods:
        - calculate_event_avg_time: Computes the average time between adjacent events.
        - get_events_total_count: Groups and counts events by type.
        - get_repositories_with_multiple_events: Finds repositories exceeding a threshold of events.
        - get_events_sorted_by_time: Helper method to sort events chronologically.
        - _calculate_avg_time: Calculates average seconds between adjacent events.
        - get_time_diff_per_event_pair: Returns list of time differences in seconds between event pairs.
        - get_event_count_by_type: Utility method to get count for a specific event type from a grouped result.
    """

    def __init__(self, db_controller: DatabaseController) -> None:
        self._db_controller = db_controller

    def _calculate_avg_time(self, events: list[Events]) -> float:
        # Sum of the difference between two adjacent sorted events
        time_diff_per_pair = self.get_time_diff_per_event_pair(events)
        total_time_diff = sum(time_diff_per_pair)

        avg_time = total_time_diff / (len(events) - 1)
        logger.info(
            "Calculated avg time between events",
            total_time_diff=total_time_diff,
            events_count=len(events),
            avg_time=avg_time,
        )
        return avg_time

    @staticmethod
    def get_time_diff_per_event_pair(events: list[Events]) -> list[float]:
        return [
            (events[idx + 1].created_at - events[idx].created_at).total_seconds()
            for idx in range(len(events) - 1)
        ]

    async def get_events_sorted_by_time(
        self, params: EventAvgTimeMetricRequest
    ) -> list[Events]:
        events = await self._db_controller.get_events_by_type(**params.model_dump())
        return sorted(events, key=lambda x: x.created_at)

    async def calculate_event_avg_time(
        self, params: EventAvgTimeMetricRequest
    ) -> EventAvgTimeMetricResponse | None:
        events_sorted = await self.get_events_sorted_by_time(params)
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

        # Note: This method may not always return perfectly accurate results
        # if the poller is actively inserting new events during execution.
        oldest_event = await self._db_controller.get_oldest_event(params.offset)
        return TotalEventsMetricResponse(
            oldest_event_time=oldest_event.created_at if oldest_event else None,
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
    return request.app.state.metrics_controller


MetricsControllerDependency = Annotated[
    MetricsController, Depends(get_metrics_controller)
]
