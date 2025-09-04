from fastapi import APIRouter
from fastapi.responses import JSONResponse


router = APIRouter()


@router.get("/ping")
def ping() -> JSONResponse:
    return JSONResponse(content={"message": "pong"})
