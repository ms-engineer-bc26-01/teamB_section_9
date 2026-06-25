import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.core.config import Settings, settings
from app.core.logging import logger, setup_logging
from app.core.redis import close_redis, ping_redis

setup_logging(settings.LOG_LEVEL)

# 開発時のみ、同一 LAN のスマホ実機（http://<private-IP>:3000）からのアクセスを
# 自動許可するための Origin 正規表現。private アドレス帯（192.168 / 10 / 172.16-31）
# かつポート 3000（Next dev）に限定する。本番では使わない。
_LAN_ORIGIN_REGEX = (
    r"http://(?:"
    r"192\.168\.\d{1,3}\.\d{1,3}"
    r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
    r"):3000"
)


def build_cors_kwargs(s: Settings) -> dict[str, object]:
    """CORS ミドルウェアの引数を組み立てる。

    本番は `BACKEND_CORS_ORIGINS` の明示許可のみ。開発時のみ LAN IP:3000 を
    `allow_origin_regex` で自動許可し、スマホ実機検証時に各自が CORS env を
    編集しなくて済むようにする。
    """
    kwargs: dict[str, object] = {
        "allow_origins": s.BACKEND_CORS_ORIGINS,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
    if s.APP_ENV.lower() == "development":
        kwargs["allow_origin_regex"] = _LAN_ORIGIN_REGEX
    return kwargs


@asynccontextmanager
async def lifespan(_app: FastAPI):
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


app.add_middleware(CORSMiddleware, **build_cors_kwargs(settings))

app.include_router(api_v1_router)
