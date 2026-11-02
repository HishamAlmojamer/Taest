from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# This value has been published in the repository and must never be used in production.
INSECURE_DEFAULT_SECRET = "e0436fceff1e125dd44e02f7862ada50fb3e4539408a337a89c18ef56dd876e8"

PRODUCTION_ENVIRONMENTS = {"production", "prod"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/warehouse_management"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_ENABLED: bool = True

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    APP_NAME: str = "ERP System"
    DEBUG: bool = False

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3001"

    # Optional one-time admin bootstrap (used on a fresh cloud database).
    BOOTSTRAP_ADMIN_USERNAME: Optional[str] = None
    BOOTSTRAP_ADMIN_PASSWORD: Optional[str] = None
    BOOTSTRAP_ADMIN_FULL_NAME: str = "System Administrator"
    BOOTSTRAP_COMPANY_NAME: str = "HM Next ERP"
    BOOTSTRAP_BRANCH_NAME: str = "Main Branch"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.strip().lower() in PRODUCTION_ENVIRONMENTS

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


def validate_settings(s: Settings) -> None:
    if len(s.JWT_SECRET or "") < 32:
        raise RuntimeError("JWT_SECRET must be at least 32 characters long")
    if s.JWT_ALGORITHM not in {"HS256", "HS384", "HS512"}:
        raise RuntimeError(f"Unsupported JWT_ALGORITHM: {s.JWT_ALGORITHM}")
    if s.is_production:
        if s.JWT_SECRET == INSECURE_DEFAULT_SECRET:
            raise RuntimeError(
                "JWT_SECRET is the insecure default value; generate a unique secret for production"
            )
        if s.JWT_SECRET.lower().startswith(("change_me", "changeme", "replace-", "replace_with")):
            raise RuntimeError("JWT_SECRET is still a placeholder value")
        if s.DEBUG:
            raise RuntimeError("DEBUG must be disabled in production")
    if s.BOOTSTRAP_ADMIN_USERNAME and not s.BOOTSTRAP_ADMIN_PASSWORD:
        raise RuntimeError("BOOTSTRAP_ADMIN_PASSWORD is required when BOOTSTRAP_ADMIN_USERNAME is set")


settings = Settings()  # type: ignore[call-arg]
validate_settings(settings)
