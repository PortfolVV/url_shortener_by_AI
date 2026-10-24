"""Application settings.

All values can be overridden through environment variables (see ``.env.example``
in the project root). ``pydantic-settings`` performs validation and type
coercion at startup, so a misconfigured container fails fast instead of
producing runtime surprises.
"""

from functools import lru_cache
from urllib.parse import urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ------------------------------------------------------------------ app
    app_name: str = "URL Shortener API"
    environment: str = "production"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Public address used when building short links returned to clients.
    base_url: str = "http://localhost:8080"

    # ------------------------------------------------------------- postgres
    database_url: str = (
        "postgresql+asyncpg://shortener:shortener@localhost:5432/shortener"
    )
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout_seconds: int = 30
    db_echo: bool = False

    # ---------------------------------------------------------------- redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50
    redis_socket_timeout_seconds: int = 5

    # Fixed lifetime of links created by anonymous users (business rule #1).
    anonymous_link_ttl_seconds: int = 60 * 60 * 24 * 7  # 7 days
    short_code_length: int = 7
    short_code_max_attempts: int = 10

    # -------------------------------------------------------------- security
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # ----------------------------------------------------------- validation
    # DNS resolution is always enforced. The optional HTTP probe rejects URLs
    # whose host resolves but where no HTTP server accepts a connection.
    url_http_check_enabled: bool = True
    url_check_timeout_seconds: float = 5.0
    # Never set this to true in a public deployment: it allows SSRF to
    # localhost / private networks through shortened links.
    allow_private_hosts: bool = False

    # ---------------------------------------------------------- rate limits
    rate_limit_enabled: bool = True
    link_creation_rate_limit: str = "10/minute"
    login_rate_limit: str = "10/minute"
    register_rate_limit: str = "5/minute"
    rate_limit_redis_db: int = 2

    # ------------------------------------------------------------------ web
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost",
    ]

    # --------------------------------------------------------------- stats
    stats_clicks_page_size: int = 200

    @property
    def rate_limit_storage_uri(self) -> str:
        """Point the limiter at a dedicated Redis database."""
        parts = urlsplit(self.redis_url)
        return urlunsplit(
            (parts.scheme, parts.netloc, f"/{self.rate_limit_redis_db}", "", "")
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
