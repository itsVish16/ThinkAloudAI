import os
import dotenv
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env
if os.path.exists(".env"):
    dotenv.load_dotenv(".env")
elif os.path.exists("../.env"):
    dotenv.load_dotenv("../.env")
else:
    dotenv.load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    FIREWORKS_BASE_URL: str = Field(
        default="https://api.fireworks.ai/inference/v1",
        validation_alias=AliasChoices("FIREWORKS_BASE_URL", "fireworks_base_url")
    )
    FIREWORKS_API_KEY: str = Field(
        default="",
        validation_alias=AliasChoices("FIREWORKS_API_KEY", "fireworks_api_key", "OPENAI_API_KEY", "openai_api_key")
    )
    FIREWORKS_MODEL: str = Field(
        default="accounts/fireworks/routers/glm-5p2-fast",
        validation_alias=AliasChoices("FIREWORKS_MODEL", "fireworks_model")
    )

    JWT_SECRET_KEY: str = Field(
        default="dev-secret-key-change-me",
        validation_alias=AliasChoices("JWT_SECRET_KEY", "SECRET_KEY", "jwt_secret_key", "secret_key")
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        validation_alias=AliasChoices("JWT_ALGORITHM", "algorithm", "jwt_algorithm")
    )

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://thinkaloud:thinkaloud_dev@localhost:5432/main_service",
        validation_alias=AliasChoices("DATABASE_URL", "MAIN_SERVICE_DATABASE_URL", "database_url")
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/1",
        validation_alias=AliasChoices("REDIS_URL", "redis_url")
    )
    RABBITMQ_URL: str = Field(
        default="amqp://guest:guest@localhost:5672/",
        validation_alias=AliasChoices("RABBITMQ_URL", "rabbitmq_url")
    )
    E2B_API_KEY: str = ""
    OPIK_API_KEY: str = ""
    OPIK_WORKSPACE: str = "default"
    OPIK_PROJECT_NAME: str = "ThinkAloud.ai"
    SPEECHMATICS_API_KEY: str = ""
    USER_SERVICE_URL: str = "http://localhost:8000"
    TAVILY_API_KEY: str = ""
    ADMIN_EMAILS: str = ""
    CORS_ALLOWED_ORIGINS: str = (
        "https://thinkaloudai.tech,https://www.thinkaloudai.tech,http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000"
    )

    def model_post_init(self, __context) -> None:
        if not self.FIREWORKS_API_KEY:
            self.FIREWORKS_API_KEY = (
                os.environ.get("FIREWORKS_API_KEY")
                or os.environ.get("OPENAI_API_KEY")
                or ""
            )
        self.FIREWORKS_API_KEY = self.FIREWORKS_API_KEY.strip().strip("'\"")

        if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY == "dev-secret-key-change-me":
            env_secret = (
                os.environ.get("JWT_SECRET_KEY")
                or os.environ.get("SECRET_KEY")
                or os.environ.get("jwt_secret_key")
                or os.environ.get("secret_key")
            )
            if env_secret:
                self.JWT_SECRET_KEY = env_secret
        if not self.JWT_SECRET_KEY:
            self.JWT_SECRET_KEY = "dev-secret-key-change-me"
        self.JWT_SECRET_KEY = self.JWT_SECRET_KEY.strip().strip("'\"")

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
        return origins or ["http://localhost:5173"]


settings = Settings()
