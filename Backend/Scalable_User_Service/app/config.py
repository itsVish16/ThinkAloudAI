import os
from functools import cached_property
from os import cpu_count
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    debug: bool = False
    DATABASE_URL: str = "postgresql+asyncpg://thinkaloud:thinkaloud_dev@localhost:5432/user_service"
    REDIS_URL: str = "redis://localhost:6379/0"
    db_pool_size: int = 20
    db_max_overflow: int = 20
    db_pool_timeout: int = 10
    redis_max_connections: int = 100

    enable_rate_limiting: bool = True
    rate_limit_trust_proxy_headers: bool = False
    rate_limit_signup: str = "5/minute"
    rate_limit_login: str = "10/minute"
    rate_limit_refresh: str = "10/minute"
    rate_limit_forgot_password: str = "5/minute"
    rate_limit_reset_password: str = "5/minute"
    rate_limit_verify_email: str = "5/minute"
    rate_limit_resend_verification: str = "5/minute"

    profile_cache_ttl_seconds: int = 300
    otp_ttl_seconds: int = 900
    max_login_attempts: int = 5
    login_lockout_seconds: int = 900

    bcrypt_concurrency: int = cpu_count() or 4

    JWT_SECRET_KEY: str = Field(
        default="dev-secret-key-change-me",
        validation_alias=AliasChoices("JWT_SECRET_KEY", "SECRET_KEY", "jwt_secret_key", "secret_key")
    )
    SECRET_KEY: str | None = None
    algorithm: str = "HS256"
    jwt_issuer: str = "scalable-user-service"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 10080

    def model_post_init(self, __context) -> None:
        if self.SECRET_KEY and self.JWT_SECRET_KEY == "dev-secret-key-change-me":
            self.JWT_SECRET_KEY = self.SECRET_KEY
        if self.JWT_SECRET_KEY == "dev-secret-key-change-me":
            env_secret = os.environ.get("JWT_SECRET_KEY") or os.environ.get("SECRET_KEY")
            if env_secret:
                self.JWT_SECRET_KEY = env_secret

    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    sqs_email_queue_url: str = ""
    resend_api_key: str = ""
    email_from: str = "noreply@example.com"
    frontend_base_url: str = "http://localhost:3000"
    email_delivery_enabled: bool = False
    cors_allowed_origins: str = Field(
        default="https://thinkaloudai.tech,https://www.thinkaloudai.tech,http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000",
        validation_alias=AliasChoices("CORS_ALLOWED_ORIGINS", "cors_allowed_origins")
    )

    @cached_property
    def cors_allowed_origins_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]
        return origins or ["http://localhost:3000"]


settings = Settings()
