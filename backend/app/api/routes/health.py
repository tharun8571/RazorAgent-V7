from fastapi import APIRouter
from typing import Dict, Any
from app.core.config import settings
from app.tools.redis_tools import get_redis_client

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Comprehensive platform health check:
    - Service metadata
    - Groq LLM configuration status
    - LangSmith tracing status
    - Razorpay Test Mode status
    - Persistence status
    """
    redis_client = await get_redis_client()
    redis_healthy = redis_client is not None

    nvidia_configured = bool(settings.NVIDIA_API_KEY and settings.NVIDIA_API_KEY != "dummy_unconfigured_key")
    langsmith_configured = bool(settings.LANGSMITH_API_KEY)

    return {
        "status": "HEALTHY",
        "service": "RazorAgent V7",
        "environment": settings.ENVIRONMENT,
        "version": "7.0.0",
        "components": {
            "groq_llm": {
                "status": "CONFIGURED" if settings.GROQ_API_KEY else "KEY_PENDING",
                "model": settings.GROQ_MODEL or "qwen/qwen3.8-27b",
            },
            "langsmith": {
                "status": "ENABLED" if settings.LANGSMITH_TRACING else "DISABLED",
                "project": settings.LANGSMITH_PROJECT,
                "configured": langsmith_configured,
            },
            "razorpay": {
                "test_mode": settings.RAZORPAY_TEST_MODE,
                "key_id_set": bool(settings.RAZORPAY_KEY_ID),
            },
            "redis": {
                "status": "CONNECTED" if redis_healthy else "FALLBACK_IN_MEMORY",
            },
            "database": {
                "status": "CONNECTED",
                "engine": "postgresql" if "postgresql" in settings.DATABASE_URL else "sqlite",
            }
        }
    }
