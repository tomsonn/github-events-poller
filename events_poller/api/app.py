from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse

from events_poller.api.endpoints import metrics, visualization
from events_poller.controllers.database import DatabaseController
from events_poller.controllers.metrics import CalculationFailedError, MetricsController
from events_poller.database.engine import Database, DatabaseError
from events_poller.settings import DatabaseConfig


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Create one DB object for the whole app's lifespan
    # Close all the connections after shutdown
    db = Database(DatabaseConfig())
    db_controller = DatabaseController(db)
    metrics_controller = MetricsController(db_controller)

    app.state.metrics_controller = metrics_controller

    try:
        yield
    finally:
        await db.close_connection()


app = FastAPI(
    title="GitHub event poller API",
    description="API serving various metrics related to GitHub events with an option to visualize them.",
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
            "error": "Not enough data for desired combination of input parameters in order to calculate the metric.",
        },
    )


@app.exception_handler(DatabaseError)
async def database_connection_exception_handler(
    request: Request, exc: DatabaseError
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": "Database connection error",
        },
    )


# go to docs, when user doesn't specify exact path
@app.get("/", include_in_schema=False)
async def root(request: Request) -> RedirectResponse:
    return RedirectResponse(url=request.app.docs_url, status_code=308)


app.include_router(metrics.router, tags=["metrics"], prefix="/metrics")
app.include_router(
    visualization.router, tags=["visualization"], prefix="/visualization"
)
