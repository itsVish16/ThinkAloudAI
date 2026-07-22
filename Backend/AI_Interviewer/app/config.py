import os
import dotenv

dotenv.load_dotenv(".env.local", override=True)

class Config:
    LIVEKIT_URL = os.getenv("LIVEKIT_URL")
    LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
    LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
    SPEECHMATICS_API_KEY = os.getenv("SPEECHMATICS_API_KEY")

    # LLM Settings (OpenAI-compatible: Fireworks, Gemini, Groq, etc.)
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "accounts/fireworks/models/llama-v3p1-70b-instruct")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.fireworks.ai/inference/v1")

    # External User Service Config (defaults assume the unified docker stack)
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8000")
    USER_SERVICE_JWT_SECRET = os.getenv("USER_SERVICE_JWT_SECRET", "default-fallback-only-for-dev")
    USER_SERVICE_JWT_ALGORITHM = os.getenv("USER_SERVICE_JWT_ALGORITHM", "HS256")
    
    # Main Service Config (defaults assume the unified docker stack)
    MAIN_SERVICE_URL = os.getenv("MAIN_SERVICE_URL", "http://localhost:8001")

    # Dev mode: bypass auth when User Service is down
    AUTH_BYPASS = os.getenv("AUTH_BYPASS", "false").lower() == "true"
    CORS_ALLOWED_ORIGINS = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000",
    )

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
        return origins or ["http://localhost:5173"]

    # Database & Events
    # NOTE: Postgres default matches the unified docker stack; the SQLite fallback
    # was removed to avoid silently storing interview data in the wrong place.
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://thinkaloud:thinkaloud_dev@localhost:5432/interviewer_service")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/2")

settings = Config()
