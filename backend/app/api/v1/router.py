from fastapi import APIRouter

from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.clothes import router as clothes_router
from app.api.v1.routers.regions import router as regions_router
from app.api.v1.routers.weather import router as weather_router
from app.api.v1.schemas.health import HealthResponse

router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="backend")


router.include_router(auth_router)
router.include_router(clothes_router)
router.include_router(regions_router)
router.include_router(weather_router)
