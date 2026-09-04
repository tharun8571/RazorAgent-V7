from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Always resolve .env relative to this file's location (backend/app/core/ -> backend/)
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment mode (development/test/production)")
    APP_NAME: str = "RazorAgent V7"
    DEBUG: bool = True

    # NVIDIA / Kimi Configuration
    NVIDIA_API_KEY: str = Field(
        default="",
        description="NVIDIA NIM API key"
    )
    NVIDIA_MODEL: str = Field(
        default="moonshotai/kimi-k3",
        description="Configured ChatNVIDIA model name"
    )
    NVIDIA_TEMPERATURE: float = Field(default=0.2, description="Temperature for agent structured reasoning")
    NVIDIA_MAX_TOKENS: int = Field(default=16384, description="Max completion tokens for ChatNVIDIA")
    NVIDIA_TIMEOUT_SECONDS: int = Field(default=30, description="Timeout for NVIDIA LLM API requests")

    # Groq Configuration (Legacy Fallback)
    GROQ_API_KEY: Optional[str] = Field(default=None, description="Groq API key for LLM intelligence")
    GROQ_MODEL: str = Field(default="llama-3.1-8b-instant", description="Configured Groq model name")
    GROQ_TEMPERATURE: float = Field(default=0.1, description="Temperature for agent structured reasoning")
    GROQ_TIMEOUT_SECONDS: int = Field(default=30, description="Timeout for Groq LLM API requests")

    # LangSmith Observability
    LANGSMITH_TRACING: bool = Field(default=True, description="Enable LangSmith distributed tracing")
    LANGSMITH_API_KEY: Optional[str] = Field(default=None, description="LangSmith API key")
    LANGSMITH_PROJECT: str = Field(default="razoragent-v7", description="LangSmith project name")
    LANGSMITH_ENDPOINT: str = Field(default="https://api.smith.langchain.com", description="LangSmith endpoint")

    # Razorpay Configuration (Test Mode)
    RAZORPAY_KEY_ID: Optional[str] = Field(default=None, description="Razorpay Key ID")
    RAZORPAY_KEY_SECRET: Optional[str] = Field(default=None, description="Razorpay Key Secret")
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = Field(default=None, description="Webhook signing secret")
    RAZORPAY_TEST_MODE: bool = Field(default=True, description="Enforce Test Mode operations")

    # Persistence & Caching
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./razoragent.db",
        description="SQLAlchemy async DB connection URL (PostgreSQL or SQLite)"
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for locks and event streams"
    )

    # Safety and Policy Boundaries (Deterministic Limits)
    MAX_TRANSACTION_AMOUNT_INR: float = Field(
        default=500000.0,
        description="Maximum allowed transaction amount in INR before requiring hard executive override"
    )
    MAX_AUTO_RETRIES: int = Field(
        default=3,
        description="Hard ceiling for automatic executor retries"
    )
    HIGH_RISK_THRESHOLD: float = Field(
        default=0.75,
        description="Risk score above which human approval is mandatorily enforced"
    )
    IDEMPOTENCY_EXPIRY_SECONDS: int = Field(
        default=86400,
        description="TTL for idempotency keys"
    )

    # Security
    SECRET_KEY: str = Field(
        default="razoragent-insecure-default-secret-change-in-production",
        description="Application secret key"
    )


settings = Settings()

# Automatically sync settings to os.environ for LangChain/LangGraph distributed tracing
import os
if settings.LANGSMITH_TRACING and settings.LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
    os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT

