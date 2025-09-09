from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from events_poller.api.endpoints import metrics, visualization
from events_poller.controllers.database import DatabaseController
from events_poller.controllers.metrics import CalculationFailedError, MetricsController
from events_poller.database.engine import Database
from events_poller.settings import DatabaseConfig


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Create one DB object for the whole app's lifespan
    # Close all the connections after shutdown
    db = Database(DatabaseConfig())
    db_controller = DatabaseController(db)
    metrics_controller = MetricsController(db_controller)

    app.state.controller = metrics_controller

    try:
        yield
    finally:
        await db.close_connection()


app = FastAPI(
    title="GitHub event poller API",
    description="API serving various metrics related to GitHub events",
    lifespan=lifespan,
)


@app.exception_handler(CalculationFailedError)
async def calculation_failed_exception_handler(
    request: Request, exc: CalculationFailedError
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "repository_name": request.query_params.get("repository_name") or "all",
            "action": request.query_params.get("action") or "all",
            "event_type": request.query_params.get("event_type"),
            "message": "Not enough data for desired combination of input parameters in order to calculate the metric.",
        },
    )


app.include_router(metrics.router, tags=["metrics"], prefix="/metrics")
app.include_router(visualization.router, tags=["visualization"])
