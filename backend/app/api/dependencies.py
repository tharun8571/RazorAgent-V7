from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.repositories.payments import PaymentRepository
from app.db.repositories.agents import AgentRepository
from app.db.repositories.incidents import IncidentRepository
from app.monitoring.incident_manager import IncidentManager


async def get_payment_repo(session: AsyncSession = Depends(get_db)) -> PaymentRepository:
    return PaymentRepository(session)


async def get_agent_repo(session: AsyncSession = Depends(get_db)) -> AgentRepository:
    return AgentRepository(session)


async def get_incident_repo(session: AsyncSession = Depends(get_db)) -> IncidentRepository:
    return IncidentRepository(session)


async def get_incident_manager(session: AsyncSession = Depends(get_db)) -> IncidentManager:
    return IncidentManager(session)
