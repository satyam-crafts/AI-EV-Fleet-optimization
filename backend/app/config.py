"""Application Configuration

Provides environment-based configuration using Pydantic Settings.
Never hardcodes secrets.
"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for the EV Fleet Optimization Platform."""

    # Application settings
    APP_NAME: str = "AI Energy & EV Fleet Optimization Agent"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS settings — include common local dev origins; production can set ALLOWED_ORIGINS=*
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # AI & LLM Provider settings
    LLM_PROVIDER: str = "template"  # 'template', 'openai', 'gemini'
    OPENAI_API_KEY: str = Field(default="", repr=False)
    GEMINI_API_KEY: str = Field(default="", repr=False)
    ANTHROPIC_API_KEY: str = Field(default="", repr=False)
    LLM_MODEL: str = "gpt-4o-mini"

    # Default Fleet Constraints
    DEFAULT_MIN_SOC_BUFFER: float = 15.0  # % SOC minimum safety floor
    DEFAULT_MAX_SOC_TARGET: float = 90.0  # % SOC maximum daily operational ceiling
    DEFAULT_CHARGING_EFFICIENCY: float = 0.92  # 92% typical charger-to-battery efficiency
    OPTIMIZATION_SOLVER: str = "heuristic"  # 'heuristic', 'linear'

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
