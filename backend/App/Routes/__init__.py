from fastapi import APIRouter
from .health import router as health_router
from .scan_route import router as scan_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(scan_router)