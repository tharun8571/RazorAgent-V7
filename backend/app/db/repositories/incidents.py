import json
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from app.db.models import Incident, RecoveryAction, utcnow


class IncidentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_incident(
        self,
        incident_id: str,
        title: str,
        severity: str = "MEDIUM",
        detected_by: str = "monitor_agent",
        root_cause: Optional[str] = None,
        evidence: Optional[Dict[str, Any]] = None,
        recovery_plan: Optional[Dict[str, Any]] = None,
        human_review_required: bool = False,
        status: str = "OPEN"
    ) -> Incident:
        incident = Incident(
            incident_id=incident_id,
            title=title,
            severity=severity,
            status=status,
            detected_by=detected_by,
            root_cause=root_cause,
            evidence_json=json.dumps(evidence or {}),
            recovery_plan_json=json.dumps(recovery_plan or {}),
            human_review_required=human_review_required,
        )
        self.session.add(incident)
        await self.session.flush()
        return incident

    async def get_incident(self, incident_id: str) -> Optional[Incident]:
        result = await self.session.execute(select(Incident).where(Incident.incident_id == incident_id))
        return result.scalar_one_or_none()

    async def update_incident(
        self,
        incident_id: str,
        status: Optional[str] = None,
        root_cause: Optional[str] = None,
        recovery_plan: Optional[Dict[str, Any]] = None,
        recovery_result: Optional[Dict[str, Any]] = None,
        resolved: bool = False,
    ) -> Optional[Incident]:
        incident = await self.get_incident(incident_id)
        if incident:
            if status is not None:
                incident.status = status
            if root_cause is not None:
                incident.root_cause = root_cause
            if recovery_plan is not None:
                incident.recovery_plan_json = json.dumps(recovery_plan)
            if recovery_result is not None:
                incident.recovery_result_json = json.dumps(recovery_result)
            if resolved:
                incident.resolved_at = utcnow()
            self.session.add(incident)
            await self.session.flush()
        return incident

    async def add_recovery_action(
        self,
        action_id: str,
        incident_id: str,
        action_type: str,
        status: str = "PENDING",
        parameters: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        executed_by: str = "recovery_agent",
    ) -> RecoveryAction:
        action = RecoveryAction(
            action_id=action_id,
            incident_id=incident_id,
            action_type=action_type,
            status=status,
            parameters_json=json.dumps(parameters or {}),
            result_json=json.dumps(result or {}),
            executed_by=executed_by,
        )
        self.session.add(action)
        await self.session.flush()
        return action

    async def list_incidents(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Incident]:
        stmt = select(Incident)
        if status:
            stmt = stmt.where(Incident.status == status)
        if severity:
            stmt = stmt.where(Incident.severity == severity)
        stmt = stmt.order_by(desc(Incident.created_at)).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
