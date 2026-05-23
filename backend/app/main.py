from fastapi import APIRouter, FastAPI

from app.schemas.health import HealthResponse

app = FastAPI(
    title="Closet Management API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

api_v1 = APIRouter(prefix="/api/v1")


@api_v1.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="backend")


app.include_router(api_v1)
