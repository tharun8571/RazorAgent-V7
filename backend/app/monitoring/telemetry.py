import os
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.security import sanitize_for_llm
from app.core.logging import logger


def build_trace_config(
    run_name: str,
    request_id: str,
    payment_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Constructs LangSmith tracing configuration dictionary with safe metadata and tags.
    Ensures zero secret leakage.
    """
    default_tags = ["razoragent-v7", f"env:{settings.ENVIRONMENT}"]
    if agent_name:
        default_tags.append(f"agent:{agent_name}")
    if tags:
        default_tags.extend(tags)

    safe_metadata = {
        "request_id": request_id,
        "payment_id": payment_id,
        "environment": settings.ENVIRONMENT,
        "workflow_version": "7.0.0",
        "groq_model": settings.GROQ_MODEL,
    }
    if metadata:
        safe_metadata.update(sanitize_for_llm(metadata))

    return {
        "run_name": run_name,
        "tags": default_tags,
        "metadata": safe_metadata,
    }


def get_langsmith_trace_url(trace_id: Optional[str] = None) -> Optional[str]:
    """Returns a direct link to the LangSmith project / trace if configured."""
    if not trace_id:
        return f"https://smith.langchain.com/projects/{settings.LANGSMITH_PROJECT}"
    return f"https://smith.langchain.com/o/default/projects/p/{settings.LANGSMITH_PROJECT}/r/{trace_id}"
