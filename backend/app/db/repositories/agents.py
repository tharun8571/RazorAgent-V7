import json
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from app.db.models import AgentRun, AgentEvent, utcnow


class AgentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_run(
        self,
        run_id: str,
        request_id: str,
        payment_id: Optional[str] = None,
        current_agent: str = "payment_agent",
        state: Optional[Dict[str, Any]] = None,
        langsmith_trace_id: Optional[str] = None,
    ) -> AgentRun:
        run = AgentRun(
            run_id=run_id,
            request_id=request_id,
            payment_id=payment_id,
            status="running",
            current_agent=current_agent,
            state_json=json.dumps(state or {}),
            langsmith_trace_id=langsmith_trace_id,
        )
        self.session.add(run)
        await self.session.flush()
        return run

    async def get_run(self, run_id: str) -> Optional[AgentRun]:
        result = await self.session.execute(select(AgentRun).where(AgentRun.run_id == run_id))
        return result.scalar_one_or_none()

    async def get_by_request_id(self, request_id: str) -> Optional[AgentRun]:
        result = await self.session.execute(select(AgentRun).where(AgentRun.request_id == request_id))
        return result.scalar_one_or_none()

    async def update_run(
        self,
        run_id: str,
        status: Optional[str] = None,
        current_agent: Optional[str] = None,
        state: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        langsmith_trace_id: Optional[str] = None,
        completed: bool = False,
    ) -> Optional[AgentRun]:
        run = await self.get_run(run_id)
        if run:
            if status is not None:
                run.status = status
            if current_agent is not None:
                run.current_agent = current_agent
            if state is not None:
                run.state_json = json.dumps(state)
            if error is not None:
                run.error = error
            if langsmith_trace_id is not None:
                run.langsmith_trace_id = langsmith_trace_id
            if completed:
                run.completed_at = utcnow()
            self.session.add(run)
            await self.session.flush()
        return run

    async def record_event(
        self,
        event_id: str,
        request_id: str,
        agent_name: str,
        event_type: str,
        run_id: Optional[str] = None,
        severity: str = "INFO",
        payload: Optional[Dict[str, Any]] = None,
    ) -> AgentEvent:
        event = AgentEvent(
            event_id=event_id,
            run_id=run_id,
            request_id=request_id,
            agent_name=agent_name,
            event_type=event_type,
            severity=severity,
            payload_json=json.dumps(payload or {}),
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def list_runs(self, limit: int = 50, offset: int = 0) -> List[AgentRun]:
        stmt = select(AgentRun).order_by(desc(AgentRun.started_at)).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_events(self, limit: int = 100, offset: int = 0, agent_name: Optional[str] = None) -> List[AgentEvent]:
        stmt = select(AgentEvent)
        if agent_name:
            stmt = stmt.where(AgentEvent.agent_name == agent_name)
        stmt = stmt.order_by(desc(AgentEvent.timestamp)).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
