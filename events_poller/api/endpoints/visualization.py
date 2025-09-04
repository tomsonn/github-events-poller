from fastapi import APIRouter
from fastapi.responses import JSONResponse


router = APIRouter()


@router.get("/visualize")
def visualize_metric() -> JSONResponse:
    return JSONResponse(content={"message": "pong-visualize"})
