from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    APP_ENV: str = Field(default="development", alias="APP_ENV")
    AUTH_BYPASS_ENABLED: bool = False
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    SUPABASE_JWT_AUDIENCE: str = "authenticated"
    SUPABASE_JWKS_CACHE_TTL_SECONDS: int = 600
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-5"

    model_config = SettingsConfigDict(env_file=".env", populate_by_name=True)


settings = Settings()
