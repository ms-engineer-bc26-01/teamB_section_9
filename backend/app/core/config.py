from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    APP_ENV: str = Field(default="development", alias="APP_ENV")
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )
    AUTH_BYPASS_ENABLED: bool = False
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    # サーバ側からの Storage アップロードに使う（RLS をバイパスする service role key）。
    SUPABASE_SERVICE_ROLE_KEY: str | None = None
    SUPABASE_JWT_AUDIENCE: str = "authenticated"
    SUPABASE_JWKS_CACHE_TTL_SECONDS: int = 600
    # コラージュ画像・服画像を保存する Supabase Storage バケット（バケット規約を共有）。
    SUPABASE_STORAGE_BUCKET: str = "clothes-images"
    # Storage アップロードのタイムアウト（秒）。OpenAI 側 timeout とは責務分離。
    SUPABASE_STORAGE_TIMEOUT_SECONDS: float = 30.0
    LOG_LEVEL: str = Field(default="INFO")
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-5-nano"
    OPENAI_IMAGE_MODEL: str = "gpt-image-1-mini"
    OPENAI_IMAGE_SIZE: str = "1024x1024"
    # 画像生成の品質（low / medium / high / auto）。低いほど高速・低コスト。
    # コラージュは小さく表示するサムネイル用途なので medium を既定とし、
    # 生成時間を抑える（未指定だと auto＝高品質寄りで最も遅くなるため明示する）。
    OPENAI_IMAGE_QUALITY: Literal["low", "medium", "high", "auto"] = "medium"
    # 画像生成 API 呼び出しのタイムアウト（秒）。保存APIの長時間ブロックを防ぐ。
    OPENAI_IMAGE_TIMEOUT_SECONDS: float = 60.0

    # Redis
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    REDIS_WEATHER_TTL_SECONDS: int = Field(default=1800)  # 天気キャッシュ 30分
    REDIS_OUTFIT_TTL_SECONDS: int = Field(default=86400)  # コーデキャッシュ 24時間

    model_config = SettingsConfigDict(
        env_file=".env",
        populate_by_name=True,
        extra="ignore",
    )


settings = Settings()


def auth_bypass_misconfigured(s: Settings) -> bool:
    """認証バイパスが development 以外で有効になっている矛盾設定かを判定する。

    `_is_auth_bypass_enabled`（dependencies/auth.py）が development 限定のため、
    本番で AUTH_BYPASS_ENABLED=true でも実際の認証スキップは発動しない。
    ただし「本番なのに true」という設定の取り違えは事故の温床なので、
    起動時にこれを検知して fail-fast するための判定。
    """
    return s.AUTH_BYPASS_ENABLED and s.APP_ENV.lower() != "development"
