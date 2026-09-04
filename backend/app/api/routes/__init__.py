"""API route registrations."""
from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.payments import router as payments_router
from app.api.routes.agents import router as agents_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.monitoring import router as monitoring_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(payments_router, prefix="/payments", tags=["Payments"])
api_router.include_router(agents_router, prefix="/agents", tags=["Agents"])
api_router.include_router(incidents_router, prefix="/incidents", tags=["Incidents"])
api_router.include_router(monitoring_router, prefix="/monitoring", tags=["Monitoring"])

__all__ = ["api_router"]
