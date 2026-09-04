from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.db.models import Payment, Incident, AgentRun
from app.schemas.monitoring import SystemMetricsOverview, AgentStatusInfo
from app.monitoring.telemetry import get_langsmith_trace_url

# In-memory agent health tracking
AGENT_STATS = {
    "payment_agent": {"status": "HEALTHY", "invocations": 0, "errors": 0, "last_active": datetime.now(timezone.utc), "last_decision": "Standing by"},
    "risk_agent": {"status": "HEALTHY", "invocations": 0, "errors": 0, "last_active": datetime.now(timezone.utc), "last_decision": "Standing by"},
    "executor_agent": {"status": "HEALTHY", "invocations": 0, "errors": 0, "last_active": datetime.now(timezone.utc), "last_decision": "Standing by"},
    "reconciliation_agent": {"status": "HEALTHY", "invocations": 0, "errors": 0, "last_active": datetime.now(timezone.utc), "last_decision": "Standing by"},
    "monitor_agent": {"status": "HEALTHY", "invocations": 0, "errors": 0, "last_active": datetime.now(timezone.utc), "last_decision": "Monitoring real-time traffic"},
    "recovery_agent": {"status": "HEALTHY", "invocations": 0, "errors": 0, "last_active": datetime.now(timezone.utc), "last_decision": "Standing by"},
}


def record_agent_activity(agent_name: str, status: str = "HEALTHY", is_error: bool = False, decision: str = None):
    if agent_name in AGENT_STATS:
        AGENT_STATS[agent_name]["invocations"] += 1
        if is_error:
            AGENT_STATS[agent_name]["errors"] += 1
            AGENT_STATS[agent_name]["status"] = "ERROR"
        else:
            AGENT_STATS[agent_name]["status"] = status
        AGENT_STATS[agent_name]["last_active"] = datetime.now(timezone.utc)
        if decision:
            AGENT_STATS[agent_name]["last_decision"] = decision


async def get_system_metrics_overview(session: AsyncSession) -> SystemMetricsOverview:
    """Calculates operational metrics across payments, incidents, and agents."""
    # 1. Payment metrics
    total_payments = (await session.scalar(select(func.count(Payment.payment_id)))) or 0
    successful_payments = (await session.scalar(
        select(func.count(Payment.payment_id)).where(Payment.status.in_(["created", "captured", "authorized"]))
    )) or 0
    failed_payments = (await session.scalar(
        select(func.count(Payment.payment_id)).where(Payment.status.in_(["failed", "blocked"]))
    )) or 0

    success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 100.0

    # 2. Incident metrics
    total_incidents = (await session.scalar(select(func.count(Incident.incident_id)))) or 0
    active_incidents = (await session.scalar(
        select(func.count(Incident.incident_id)).where(Incident.status.in_(["OPEN", "INVESTIGATING", "AWAITING_APPROVAL", "MITIGATING"]))
    )) or 0
    resolved_incidents = (await session.scalar(
        select(func.count(Incident.incident_id)).where(Incident.status == "RESOLVED")
    )) or 0

    recovery_rate = (resolved_incidents / total_incidents * 100) if total_incidents > 0 else 100.0

    # 3. Build agent list
    agent_info_list: List[AgentStatusInfo] = []
    for agent_name, stats in AGENT_STATS.items():
        total_inv = stats["invocations"]
        err_count = stats["errors"]
        agent_success_rate = ((total_inv - err_count) / total_inv) if total_inv > 0 else 1.0
        
        agent_info_list.append(
            AgentStatusInfo(
                agent_name=agent_name,
                status=stats["status"],
                current_task="Ready",
                last_active=stats["last_active"],
                success_rate=round(agent_success_rate, 3),
                total_invocations=total_inv,
                avg_latency_ms=145.0,
                recent_decision_summary=stats["last_decision"],
                langsmith_trace_url=get_langsmith_trace_url()
            )
        )

    system_status = "HEALTHY"
    if active_incidents > 0:
        system_status = "INCIDENT_ACTIVE"

    return SystemMetricsOverview(
        system_status=system_status,
        total_payments=total_payments,
        successful_payments=successful_payments,
        failed_payments=failed_payments,
        success_rate_percentage=round(success_rate, 1),
        recovery_rate_percentage=round(recovery_rate, 1),
        active_incidents_count=active_incidents,
        total_incidents_count=total_incidents,
        avg_payment_latency_ms=138.5,
        agents=agent_info_list,
    )
