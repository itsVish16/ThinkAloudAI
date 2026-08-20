from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.local", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    LIVEKIT_URL: Optional[str] = "ws://localhost:7880"
    LIVEKIT_API_KEY: Optional[str] = "devkey"
    LIVEKIT_API_SECRET: Optional[str] = "secret"

    # Sarvam AI Unified Config (TTS, STT, and LLM)
    SARVAM_API_KEY: Optional[str] = None
    SARVAM_BASE_URL: str = "https://api.sarvam.ai/v1"
    SARVAM_MODEL: str = "gemma4"
    SARVAM_TTS_MODEL: str = "bulbul:v3"
    SARVAM_TTS_SPEAKER: str = "shubh"
    SARVAM_TTS_LANGUAGE: str = "en-IN"
    SARVAM_TTS_PACE: float = 1.0
    SARVAM_TTS_SAMPLE_RATE: int = 22050
    SARVAM_TTS_WS_URL: str = "wss://api.sarvam.ai/text-to-speech/ws"
    SARVAM_STT_MODEL: str = "saarika:v2.5"
    SARVAM_STT_LANGUAGE: str = "en-IN"
    SARVAM_STT_URL: Optional[str] = None

    # Single Fast LLM Mode (Defaults to Sarvam gemma4 for ultra low-latency)
    DUAL_LLM_ENABLED: bool = False

    # Fast Responder LLM
    FAST_LLM_API_KEY: str = ""
    FAST_LLM_MODEL: str = "gemma4"
    FAST_LLM_BASE_URL: str = "https://api.sarvam.ai/v1"
    FAST_LLM_MAX_TOKENS: int = 60

    # Main Reasoning LLM (Defaults to Sarvam gemma4)
    MAIN_LLM_API_KEY: str = ""
    MAIN_LLM_MODEL: str = "gemma4"
    MAIN_LLM_BASE_URL: str = "https://api.sarvam.ai/v1"

    # Fireworks AI / DeepSeek for Background Post-Interview Analysis & Grading
    FIREWORKS_API_KEY: str = ""
    FIREWORKS_BASE_URL: str = "https://api.fireworks.ai/inference/v1"
    FIREWORKS_MODEL: str = "accounts/fireworks/models/deepseek-v3"

    ANALYSIS_LLM_API_KEY: str = ""
    ANALYSIS_LLM_MODEL: str = "accounts/fireworks/models/deepseek-v3"
    ANALYSIS_LLM_BASE_URL: str = "https://api.fireworks.ai/inference/v1"

    # Legacy fallback LLM Settings (OpenAI-compatible)
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "sarvam-105b"
    LLM_BASE_URL: str = "https://api.sarvam.ai/v1"

    # External User Service Config
    USER_SERVICE_URL: str = "http://localhost:8000"
    USER_SERVICE_JWT_SECRET: Optional[str] = None
    JWT_SECRET_KEY: str = "dev-secret-key-change-me"
    JWT_ALGORITHM: str = "HS256"

    # Main Service Config
    MAIN_SERVICE_URL: str = "http://localhost:8001"

    # Dev mode: bypass auth when User Service is down
    AUTH_BYPASS: bool = False
    CORS_ALLOWED_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,https://thinkaloudai.tech,https://www.thinkaloudai.tech"
    )

    # Database & Events
    DATABASE_URL: str = "postgresql+asyncpg://thinkaloud:thinkaloud_dev@localhost:5432/interviewer_service"
    REDIS_URL: str = "redis://localhost:6379/2"
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    ADMIN_EMAILS: str = ""
    OPIK_API_KEY: Optional[str] = None
    OPIK_WORKSPACE: str = "default"
    OPIK_PROJECT_NAME: str = "ThinkAloud.ai"

    @property
    def jwt_secret(self) -> str:
        return self.USER_SERVICE_JWT_SECRET or self.JWT_SECRET_KEY

    @property
    def fast_llm_key(self) -> str:
        return self.FAST_LLM_API_KEY or self.SARVAM_API_KEY or self.LLM_API_KEY or "dummy_key"

    @property
    def fast_llm_url(self) -> str:
        return self.FAST_LLM_BASE_URL or self.SARVAM_BASE_URL or self.LLM_BASE_URL

    @property
    def main_llm_key(self) -> str:
        return self.MAIN_LLM_API_KEY or self.SARVAM_API_KEY or self.LLM_API_KEY or "dummy_key"

    @property
    def main_llm_url(self) -> str:
        return self.MAIN_LLM_BASE_URL or self.SARVAM_BASE_URL or self.LLM_BASE_URL

    @property
    def analysis_llm_key(self) -> str:
        return self.ANALYSIS_LLM_API_KEY or self.FIREWORKS_API_KEY or self.SARVAM_API_KEY or self.main_llm_key

    @property
    def analysis_llm_url(self) -> str:
        return self.ANALYSIS_LLM_BASE_URL or self.FIREWORKS_BASE_URL or self.SARVAM_BASE_URL

    @property
    def analysis_llm_model(self) -> str:
        return self.ANALYSIS_LLM_MODEL or self.FIREWORKS_MODEL or "accounts/fireworks/models/deepseek-v3"

    @property
    def cors_allowed_origins_list(self) -> List[str]:
        origins = [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
        return origins or ["http://localhost:5173"]


settings = Config()
