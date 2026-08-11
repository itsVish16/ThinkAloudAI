import os
import dotenv
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

    FIREWORKS_BASE_URL: str = "https://api.fireworks.ai/inference/v1"
    FIREWORKS_API_KEY: str = ""
    FIREWORKS_MODEL: str = "accounts/fireworks/routers/glm-5p2-fast"
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    E2B_API_KEY: str = "replace_me_in_env"
    OPIK_API_KEY: str = "replace_me_in_env"
    OPIK_WORKSPACE: str = "default"
    OPIK_PROJECT_NAME: str = "ThinkAloud.ai"
    UPSTASH_REDIS_URL: str = "redis://localhost:6379"
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"
    SPEECHMATICS_API_KEY: str = ""
    USER_SERVICE_URL: str = "http://localhost:8000"
    TAVILY_API_KEY: str = ""
    CORS_ALLOWED_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    )

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
        return origins or ["http://localhost:5173"]

settings = Settings()
