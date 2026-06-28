import time
from contextlib import asynccontextmanager
from typing import Protocol

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.core.config import auth_bypass_misconfigured, settings
from app.core.logging import logger, setup_logging
from app.core.redis import close_redis, ping_redis


class _CorsSettings(Protocol):
    """CORS 設定に必要な属性だけを表す Protocol。

    `Settings` と `SimpleNamespace` の両方に適合する。
    """

    APP_ENV: str
    BACKEND_CORS_ORIGINS: list[str]


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


def build_cors_kwargs(s: _CorsSettings) -> dict[str, object]:
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
    title="Climo API",
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
