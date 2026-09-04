from typing import Dict, Any, Optional
from app.core.logging import logger


async def notify_operator_tool(
    title: str,
    message: str,
    severity: str = "INFO",
    incident_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Sends an urgent alert/notification to human operators.
    """
    payload = {
        "title": title,
        "message": message,
        "severity": severity,
        "incident_id": incident_id,
        "details": details or {},
    }
    logger.warning(
        f"[OPERATOR ALERT] [{severity}] {title}: {message}",
        extra={"notification": payload}
    )
    return {"status": "dispatched", "notification": payload}
