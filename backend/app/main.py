import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.core.config import auth_bypass_misconfigured, settings
from app.core.logging import logger, setup_logging
from app.core.redis import close_redis, ping_redis

setup_logging(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 本番なのにバイパス有効、という矛盾設定はサイレント運用を避けるため起動を止める。
    if auth_bypass_misconfigured(settings):
        raise RuntimeError(
            "AUTH_BYPASS_ENABLED must be false unless APP_ENV=development "
            f"(APP_ENV={settings.APP_ENV!r}). 本番では必ず false にしてください。"
        )

    # 起動時に Redis 疎通を確認（キャッシュ用途のため失敗してもアプリは起動する）
    if await ping_redis():
        logger.info("redis connected (%s)", settings.REDIS_URL)
    else:
        logger.warning(
            "redis unavailable at startup (%s); caching disabled",
            settings.REDIS_URL,
        )
    yield
    await close_redis()


app = FastAPI(
    title="Closet Management API",  # TODO:アプリ名のAPIに変更
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "%s %s -> 500 (%.1fms)",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)
