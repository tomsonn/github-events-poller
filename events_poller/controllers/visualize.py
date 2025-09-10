from typing import Annotated

import plotly.graph_objects as go

from fastapi import Depends
from events_poller.controllers.metrics import MetricsControllerDependency
from events_poller.models.enum import EventTypeEnum, GraphTypeEnum
from events_poller.logger import logger
from events_poller.models.models import (
    EventAvgTimeMetricRequest,
    EventAvgTimeVisualizeRequest,
    TotalEventsMetricRequest,
)


class VisualizeController:
    """
    Controller responsible for generating interactive visualizations of GitHub event metrics using Plotly.

    This controller acts as a bridge between metric data and visual presentation.
    It leverages the MetricsController to fetch processed data and renders them into
    interactive charts such as:

    - Scatter plots with average time between events
    - Bar charts representing event type distributions

    Methods:
        - get_graph: Dispatcher method selecting the graph type to generate.
        - _get_avg_time_graph: Visualizes time differences and averages between events.
        - _get_total_count_graph: Displays a bar chart of event type counts.
    """

    def __init__(self, metrics_controller: MetricsControllerDependency):
        self._metrics_controller = metrics_controller
        self._colors = ["darkred", "darkkhaki", "darkorange"]

    async def _get_avg_time_graph(
        self, params: EventAvgTimeVisualizeRequest
    ) -> go.Figure:
        async def _get_time_diff_per_event_type(
            params: EventAvgTimeVisualizeRequest,
        ) -> list[float]:
            event_metric_param = EventAvgTimeMetricRequest(
                event_type=params.event_type,
                action=params.action,
                repository_name=params.repository_name,
            )
            events_sorted = await self._metrics_controller.get_events_sorted_by_time(
                event_metric_param
            )
            return self._metrics_controller.get_time_diff_per_event_pair(events_sorted)

        fig = go.Figure()

        events_to_plot = (
            [params.event_type] if params.event_type else list(EventTypeEnum)
        )
        for _color, _event in zip(self._colors, events_to_plot):
            _params = EventAvgTimeVisualizeRequest(
                event_type=_event,
                action=params.action,
                repository_name=params.repository_name,
            )
            time_diff_per_pair = await _get_time_diff_per_event_type(_params)
            avg_time = round(sum(time_diff_per_pair) / (len(time_diff_per_pair) - 1), 2)

            fig.add_trace(
                go.Scatter(
                    x=[i for i in range(len(time_diff_per_pair) - 1)],
                    y=time_diff_per_pair,
                    mode="markers",
                    name=f"{_event} - diff time",
                    line=dict(color=_color, width=1, dash="dot"),
                )
            )
            fig.add_hline(
                y=avg_time,
                showlegend=True,
                name=f"{_event} - avg time of {avg_time} seconds",
                line=dict(color=_color, width=1, dash="longdash"),
            )

        fig.update_layout(
            title="Average time between events",
            title_x=0.5,
            xaxis_title="Events",
            yaxis_title="Time Between Events",
            margin=dict(l=40, r=20, t=60, b=40),
            showlegend=True,
            legend_title_text="Event Type",
        )
        return fig

    async def _get_total_count_graph(
        self, params: TotalEventsMetricRequest
    ) -> go.Figure:
        events_total_count = await self._metrics_controller.get_events_total_count(
            params
        )
        event_types_real = events_total_count.events_count.model_dump(exclude="total")
        fig = go.Figure(
            go.Bar(x=list(event_types_real.keys()), y=list(event_types_real.values()))
        )
        fig.update_layout(
            title=f"Events distribution by their type within the last {params.offset} seconds",
            title_x=0.5,
            xaxis_title="Event Type",
            yaxis_title="Events Count",
            margin=dict(l=40, r=20, t=60, b=40),
        )
        return fig

    async def get_graph(
        self,
        params: EventAvgTimeVisualizeRequest | TotalEventsMetricRequest,
        graph_type: GraphTypeEnum,
    ) -> go.Figure:
        match graph_type:
            case GraphTypeEnum.AVG_TIME:
                logger.info("Requesting graph to visualize", graph_type=graph_type)
                return await self._get_avg_time_graph(params)
            case GraphTypeEnum.TOTAL_COUNT:
                logger.info("Requesting graph to visualize", graph_type=graph_type)
                return await self._get_total_count_graph(params)
            case _:
                raise ValueError


def get_visualize_controller(
    metrics_controller: MetricsControllerDependency,
) -> VisualizeController:
    return VisualizeController(metrics_controller)


VisualizeControllerDependency = Annotated[
    VisualizeController, Depends(get_visualize_controller)
]
