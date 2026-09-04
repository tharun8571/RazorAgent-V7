import os
from typing import Type, TypeVar, Optional, Any
from pydantic import BaseModel
from langchain_groq import ChatGroq
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import LLMUnavailableError, LLMStructuredOutputError

T = TypeVar("T", bound=BaseModel)


def configure_langsmith_environment():
    """Ensure LangSmith environment variables are synchronized for tracing."""
    if settings.LANGSMITH_TRACING and settings.LANGSMITH_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
        os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
    else:
        # Keep project name set even in local test runs
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT


def get_llm(temperature: Optional[float] = None, timeout: Optional[int] = None) -> ChatGroq:
    """
    Centralized factory for obtaining ultra-fast Groq LLM instance (qwen/qwen3.8-27b).
    All agents obtain their LLM through this layer.
    """
    configure_langsmith_environment()

    api_key = settings.GROQ_API_KEY
    if not api_key:
        logger.warning("GROQ_API_KEY is not set in environment. LLM invocations will raise LLMUnavailableError.")
        api_key = "dummy_unconfigured_key"

    try:
        llm = ChatGroq(
            groq_api_key=api_key,
            model_name=settings.GROQ_MODEL,
            temperature=temperature if temperature is not None else settings.GROQ_TEMPERATURE,
            request_timeout=timeout or settings.GROQ_TIMEOUT_SECONDS,
            max_tokens=350,  # Strict token budget to guarantee ultra-fast sub-second execution & 0 rate-limits
            max_retries=2,  # Retries transient 429s automatically
        )
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize Groq LLM client: {str(e)}", exc_info=True)
        raise LLMUnavailableError(f"Groq LLM initialization failed: {str(e)}")


_STRUCTURED_LLM_CACHE: dict = {}

def get_structured_llm(schema: Type[T], temperature: Optional[float] = None) -> Any:
    """
    Wraps Groq LLM with a Pydantic schema for structured output reasoning using method="json_mode".
    Uses in-memory instance caching to preserve HTTP keep-alive connection pools and prevent tool_use_failed errors.
    """
    temp = temperature if temperature is not None else settings.GROQ_TEMPERATURE
    cache_key = (schema, temp, settings.GROQ_MODEL)

    if cache_key not in _STRUCTURED_LLM_CACHE:
        base_llm = get_llm(temperature=temp)
        try:
            _STRUCTURED_LLM_CACHE[cache_key] = base_llm.with_structured_output(schema, method="json_mode")
        except Exception as e:
            logger.error(f"Failed to bind structured output schema {schema.__name__}: {str(e)}")
            raise LLMStructuredOutputError(f"Structured output schema binding failed: {str(e)}")

    return _STRUCTURED_LLM_CACHE[cache_key]
