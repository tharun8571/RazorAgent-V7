import pytest
from app.monitoring.incident_manager import IncidentManager
from app.schemas.incident import MonitoringDecision, RecoveryPlan


@pytest.mark.asyncio
async def test_incident_lifecycle_and_hitl(test_session):
    """
    Test creating an incident, proposing recovery plan, and executing human-in-the-loop approval.
    """
    mgr = IncidentManager(test_session)

    mon_decision = MonitoringDecision(
        system_status="CRITICAL_ANOMALY",
        anomaly_detected=True,
        anomaly_type="RECONCILIATION_DESYNC",
        severity="HIGH",
        root_cause="Database marked payment captured but gateway refunded it.",
        evidence={"discrepancy": "DB=captured, Gateway=refunded"},
        recommended_recovery="Rollback transaction and notify customer.",
        confidence=0.96,
        human_intervention_required=True
    )

    plan = RecoveryPlan(
        action="rollback_safe_operation",
        reason="Safely align database with gateway refund.",
        expected_effect="State synchronized.",
        risk="HIGH",
        requires_human_approval=True,
        verification_plan="Query gateway and check zero balance.",
        action_parameters={"payment_id": "pay_test_recon_01"}
    )

    # 1. Create Incident
    inc_id = await mgr.create_incident_from_monitoring(
        request_id="req_test_inc",
        title="Reconciliation Desync Detected",
        monitoring_decision=mon_decision,
        recovery_plan=plan
    )
    await test_session.commit()
    assert inc_id.startswith("inc_")

    # 2. Operator Approves (HITL)
    res = await mgr.approve_incident_recovery(
        incident_id=inc_id,
        operator_name="operator:sarah",
        reason="Verified against Razorpay console; safe to rollback."
    )
    await test_session.commit()

    assert res["status"] == "success"
    assert res["incident_id"] == inc_id
