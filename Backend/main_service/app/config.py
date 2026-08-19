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

    def model_post_init(self, __context) -> None:
        if not self.FIREWORKS_API_KEY:
            self.FIREWORKS_API_KEY = (
                os.environ.get("FIREWORKS_API_KEY")
                or os.environ.get("OPENAI_API_KEY")
                or ""
            )
        self.FIREWORKS_API_KEY = self.FIREWORKS_API_KEY.strip().strip("'\"")
    DATABASE_URL: str = "postgresql+asyncpg://thinkaloud:thinkaloud_dev@localhost:5432/main_service"
    JWT_SECRET_KEY: str = "dev-secret-key-change-me"
    JWT_ALGORITHM: str = "HS256"
    E2B_API_KEY: str = ""
    OPIK_API_KEY: str = ""
    OPIK_WORKSPACE: str = "default"
    OPIK_PROJECT_NAME: str = "ThinkAloud.ai"
    REDIS_URL: str = "redis://localhost:6379/1"
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    SPEECHMATICS_API_KEY: str = ""
    USER_SERVICE_URL: str = "http://localhost:8000"
    TAVILY_API_KEY: str = ""
    ADMIN_EMAILS: str = ""
    CORS_ALLOWED_ORIGINS: str = (
        "https://thinkaloudai.tech,https://www.thinkaloudai.tech,http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000"
    )

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
        return origins or ["http://localhost:5173"]


settings = Settings()
