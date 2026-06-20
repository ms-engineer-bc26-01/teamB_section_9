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
    # 画像生成 API 呼び出しのタイムアウト（秒）。保存APIの長時間ブロックを防ぐ。
    OPENAI_IMAGE_TIMEOUT_SECONDS: float = 60.0

    # Redis
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    REDIS_WEATHER_TTL_SECONDS: int = Field(default=1800)  # 天気キャッシュ 30分
    REDIS_OUTFIT_TTL_SECONDS: int = Field(default=86400)  # コーデキャッシュ 24時間

    model_config = SettingsConfigDict(env_file=".env", populate_by_name=True)


settings = Settings()
