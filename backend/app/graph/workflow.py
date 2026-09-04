from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from app.graph.state import RazorAgentState
from app.graph.nodes import (
    payment_node,
    risk_node,
    safety_boundary_node,
    executor_node,
    reconciliation_node,
    monitor_node,
    recovery_node,
    verification_node,
)
from app.graph.routing import (
    route_after_payment,
    route_after_risk,
    route_after_safety,
    route_after_monitor,
)
from app.monitoring.telemetry import build_trace_config
from app.core.logging import logger


def get_razoragent_workflow() -> Any:
    """
    Assembles and compiles the full RazorAgent V7 LangGraph StateGraph.
    """
    workflow = StateGraph(RazorAgentState)

    # 1. Register Nodes
    workflow.add_node("payment_node", payment_node)
    workflow.add_node("risk_node", risk_node)
    workflow.add_node("safety_boundary_node", safety_boundary_node)
    workflow.add_node("executor_node", executor_node)
    workflow.add_node("reconciliation_node", reconciliation_node)
    workflow.add_node("monitor_node", monitor_node)
    workflow.add_node("recovery_node", recovery_node)
    workflow.add_node("verification_node", verification_node)

    # 2. Define Entry Point
    workflow.set_entry_point("payment_node")

    # 3. Add Edges & Conditional Routing
    workflow.add_conditional_edges(
        "payment_node",
        route_after_payment,
        {
            "risk_node": "risk_node",
            "verification_node": "verification_node",
        }
    )

    workflow.add_conditional_edges(
        "risk_node",
        route_after_risk,
        {
            "safety_boundary_node": "safety_boundary_node",
            "monitor_node": "monitor_node",
            "verification_node": "verification_node",
        }
    )

    workflow.add_conditional_edges(
        "safety_boundary_node",
        route_after_safety,
        {
            "executor_node": "executor_node",
            "monitor_node": "monitor_node",
        }
    )

    workflow.add_edge("executor_node", "reconciliation_node")
    workflow.add_edge("reconciliation_node", "monitor_node")

    workflow.add_conditional_edges(
        "monitor_node",
        route_after_monitor,
        {
            "recovery_node": "recovery_node",
            "verification_node": "verification_node",
        }
    )

    workflow.add_edge("recovery_node", "verification_node")
    workflow.add_edge("verification_node", END)

    return workflow.compile()


# Singleton compiled graph
_compiled_app = None


def get_compiled_graph():
    global _compiled_app
    if _compiled_app is None:
        _compiled_app = get_razoragent_workflow()
    return _compiled_app


async def run_payment_workflow(initial_state: RazorAgentState) -> RazorAgentState:
    """
    Executes the multi-agent graph with LangSmith tracing metadata and tags.
    """
    app = get_compiled_graph()
    req_id = initial_state.get("request_id", "req_unknown")
    pay_id = initial_state.get("payment_id")

    trace_config = build_trace_config(
        run_name=f"RazorAgent_Workflow_{req_id}",
        request_id=req_id,
        payment_id=pay_id,
        tags=["langgraph", "multi-agent-workflow", f"customer:{initial_state.get('customer_id')}"]
    )

    logger.info(f"Starting RazorAgent workflow execution for request {req_id}")
    final_state = await app.ainvoke(initial_state, config=trace_config)
    logger.info(f"Completed RazorAgent workflow execution for request {req_id} with status {final_state.get('workflow_status')}")
    return final_state
