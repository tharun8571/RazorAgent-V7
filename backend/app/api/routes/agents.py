from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.repositories.agents import AgentRepository
from app.monitoring.metrics import AGENT_STATS
from app.monitoring.telemetry import get_langsmith_trace_url

router = APIRouter()


@router.get("/")
async def list_agents(session: AsyncSession = Depends(get_db)):
    """Returns status and metrics for all agents in the multi-agent system."""
    agent_repo = AgentRepository(session)
    recent_events = await agent_repo.list_events(limit=20)

    result = []
    for name, stats in AGENT_STATS.items():
        total = stats["invocations"]
        errs = stats["errors"]
        success_rate = ((total - errs) / total) if total > 0 else 1.0

        result.append({
            "agent_name": name,
            "status": stats["status"],
            "invocations": total,
            "errors": errs,
            "success_rate": round(success_rate, 3),
            "last_active": stats["last_active"].isoformat(),
            "last_decision": stats["last_decision"],
            "langsmith_url": get_langsmith_trace_url(),
        })
    return result


@router.get("/{agent_name}")
async def get_agent_details(agent_name: str, session: AsyncSession = Depends(get_db)):
    """Returns detailed statistics and recent events for a specific agent."""
    if agent_name not in AGENT_STATS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    agent_repo = AgentRepository(session)
    events = await agent_repo.list_events(limit=30, agent_name=agent_name)
    stats = AGENT_STATS[agent_name]

    return {
        "agent_name": agent_name,
        "status": stats["status"],
        "invocations": stats["invocations"],
        "errors": stats["errors"],
        "last_active": stats["last_active"].isoformat(),
        "last_decision": stats["last_decision"],
        "langsmith_url": get_langsmith_trace_url(),
        "recent_events": [
            {
                "event_id": e.event_id,
                "event_type": e.event_type,
                "severity": e.severity,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in events
        ]
    }
