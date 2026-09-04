import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.repositories.incidents import IncidentRepository
from app.monitoring.incident_manager import IncidentManager
from app.schemas.incident import IncidentApprovalRequest, IncidentRejectRequest
from app.monitoring.telemetry import get_langsmith_trace_url

router = APIRouter()


@router.get("/")
async def list_incidents(
    status: Optional[str] = Query(None, description="Filter by status (OPEN, AWAITING_APPROVAL, RESOLVED, etc.)"),
    severity: Optional[str] = Query(None, description="Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)"),
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db)
):
    """Lists incidents with optional filtering."""
    repo = IncidentRepository(session)
    incidents = await repo.list_incidents(status=status, severity=severity, limit=limit, offset=offset)

    return [
        {
            "incident_id": inc.incident_id,
            "title": inc.title,
            "severity": inc.severity,
            "status": inc.status,
            "detected_by": inc.detected_by,
            "root_cause": inc.root_cause,
            "human_review_required": inc.human_review_required,
            "created_at": inc.created_at.isoformat() if inc.created_at else None,
            "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
            "langsmith_trace_url": get_langsmith_trace_url(),
        }
        for inc in incidents
    ]


@router.get("/{incident_id}")
async def get_incident(
    incident_id: str,
    session: AsyncSession = Depends(get_db)
):
    """Retrieves full incident details including AI diagnosis, evidence, and recovery plan."""
    repo = IncidentRepository(session)
    inc = await repo.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    return {
        "incident_id": inc.incident_id,
        "title": inc.title,
        "severity": inc.severity,
        "status": inc.status,
        "detected_by": inc.detected_by,
        "root_cause": inc.root_cause,
        "evidence": json.loads(inc.evidence_json or "{}"),
        "recovery_plan": json.loads(inc.recovery_plan_json or "{}"),
        "recovery_result": json.loads(inc.recovery_result_json or "{}"),
        "human_review_required": inc.human_review_required,
        "created_at": inc.created_at.isoformat() if inc.created_at else None,
        "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
        "langsmith_trace_url": get_langsmith_trace_url(),
    }


@router.post("/{incident_id}/approve")
async def approve_incident(
    incident_id: str,
    body: IncidentApprovalRequest,
    session: AsyncSession = Depends(get_db)
):
    """
    Human-in-the-Loop Approval:
    Operator approves the AI-generated recovery plan. The action is executed and logged in audit trails.
    """
    mgr = IncidentManager(session)
    try:
        result = await mgr.approve_incident_recovery(
            incident_id=incident_id,
            operator_name=body.operator_name,
            reason=body.reason or "Approved by operator"
        )
        await session.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Approval execution failed: {str(e)}")


@router.post("/{incident_id}/reject")
async def reject_incident(
    incident_id: str,
    body: IncidentRejectRequest,
    session: AsyncSession = Depends(get_db)
):
    """
    Human-in-the-Loop Rejection:
    Operator rejects the AI recovery plan and provides the rationale.
    """
    mgr = IncidentManager(session)
    try:
        result = await mgr.reject_incident_recovery(
            incident_id=incident_id,
            operator_name=body.operator_name,
            reason=body.reason
        )
        await session.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
