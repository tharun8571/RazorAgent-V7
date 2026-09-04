import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.db.database import AsyncSessionLocal
from app.db.repositories.agents import AgentRepository
from app.tools.redis_tools import publish_event_tool
from app.core.security import generate_id, sanitize_for_llm
from app.core.logging import logger

_RECENT_MEMORY_EVENTS: List[Dict[str, Any]] = []


import asyncio

async def _async_persist_event(
    event_id: str,
    request_id: str,
    agent_name: str,
    event_type: str,
    run_id: Optional[str],
    severity: str,
    sanitized_payload: Dict[str, Any],
):
    """Background persistence worker -- runs off the critical latency path."""
    try:
        await publish_event_tool("agent_events_stream", {
            "event_id": event_id,
            "run_id": run_id,
            "request_id": request_id,
            "agent_name": agent_name,
            "event_type": event_type,
            "severity": severity,
            "payload": sanitized_payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        pass

    try:
        async with AsyncSessionLocal() as session:
            repo = AgentRepository(session)
            await repo.record_event(
                event_id=event_id,
                request_id=request_id,
                agent_name=agent_name,
                event_type=event_type,
                run_id=run_id,
                severity=severity,
                payload=sanitized_payload
            )
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to persist agent event to DB: {str(e)}")


async def record_agent_event(
    agent_name: str,
    event_type: str,
    request_id: str,
    severity: str = "INFO",
    run_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Persists an agent operational event to local memory buffer immediately,
    and dispatches DB & Redis persistence as non-blocking background tasks.
    """
    event_id = generate_id("evt")
    sanitized_payload = sanitize_for_llm(payload or {})
    event_data = {
        "event_id": event_id,
        "run_id": run_id,
        "request_id": request_id,
        "agent_name": agent_name,
        "event_type": event_type,
        "severity": severity,
        "payload": sanitized_payload,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # 1. Instant in-memory update for zero-latency dashboard UI polling
    _RECENT_MEMORY_EVENTS.append(event_data)
    if len(_RECENT_MEMORY_EVENTS) > 500:
        _RECENT_MEMORY_EVENTS.pop(0)

    # 2. Non-blocking background persistence (0 ms latency overhead)
    asyncio.create_task(
        _async_persist_event(
            event_id=event_id,
            request_id=request_id,
            agent_name=agent_name,
            event_type=event_type,
            run_id=run_id,
            severity=severity,
            sanitized_payload=sanitized_payload,
        )
    )

    return event_data


def get_recent_events(limit: int = 50, agent_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve recent in-memory activity events."""
    events = list(reversed(_RECENT_MEMORY_EVENTS))
    if agent_name:
        events = [e for e in events if e.get("agent_name") == agent_name]
    return events[:limit]
