from fastapi import APIRouter

from events_poller.api.endpoints import metrics, visualization


router = APIRouter()


router.include_router(metrics.router, tags=["metrics"])
router.include_router(visualization.router, tags=["visualization"])
