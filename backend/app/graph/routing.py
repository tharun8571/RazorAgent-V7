from typing import Literal
from app.graph.state import RazorAgentState


def route_after_payment(state: RazorAgentState) -> Literal["risk_node", "verification_node"]:
    """Routes based on payment agent analysis."""
    status = state.get("workflow_status")
    decision = state.get("payment_decision", {}).get("decision")
    if status in {"PAUSED_FOR_HUMAN", "REJECTED"} or decision == "REJECT":
        return "verification_node"
    return "risk_node"


def route_after_risk(state: RazorAgentState) -> Literal["safety_boundary_node", "monitor_node", "verification_node"]:
    """Routes based on risk assessment."""
    status = state.get("workflow_status")
    if status in {"BLOCKED_RISK", "PAUSED_FOR_HUMAN"}:
        return "monitor_node"
    return "safety_boundary_node"


def route_after_safety(state: RazorAgentState) -> Literal["executor_node", "monitor_node"]:
    """Routes based on deterministic safety checks."""
    if state.get("workflow_status") == "PAUSED_FOR_HUMAN":
        return "monitor_node"
    return "executor_node"


def route_after_monitor(state: RazorAgentState) -> Literal["recovery_node", "verification_node"]:
    """Routes based on whether supervisor detected an anomaly."""
    mon_decision = state.get("monitoring_decision")
    if mon_decision and mon_decision.get("anomaly_detected"):
        return "recovery_node"
    return "verification_node"
