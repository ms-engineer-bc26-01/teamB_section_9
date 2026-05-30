from fastapi import FastAPI

from app.api.v1.router import router as api_v1_router

app = FastAPI(
    title="Closet Management API",  # TODO:アプリ名のAPIに変更
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(api_v1_router)
