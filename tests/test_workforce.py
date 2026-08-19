import pytest

from omniagent.economics import ComputeCandidate
from omniagent.trust import TrustDecision
from omniagent.workforce import (
    Evidence,
    ExecutionRequest,
    ExecutionStatus,
    WorkforceOrchestrator,
)


def _request(**overrides):
    values = {
        "request_id": "req-1",
        "task_type": "lead_search",
        "payload": {"query": "abogados", "location": "Madrid"},
        "evidence": (Evidence("omniscraper", "search", "lead search requested"),),
    }
    values.update(overrides)
    return ExecutionRequest(**values)


def test_plan_selects_affordable_candidate_and_preserves_evidence():
    plan = WorkforceOrchestrator().plan(
        _request(budget=0.05),
        [
            ComputeCandidate("expensive", model="large", estimated_cost=0.10),
            ComputeCandidate("economy", model="small", estimated_cost=0.02),
        ],
        TrustDecision(approved=True, confidence=1.0),
    )

    assert plan.status is ExecutionStatus.PLANNED
    assert plan.provider == "economy"
    assert plan.evidence[0].source == "omniscraper"


def test_plan_requires_trust_by_default():
    with pytest.raises(PermissionError, match="trust decision required"):
        WorkforceOrchestrator().plan(_request(), [ComputeCandidate("provider")])


def test_plan_rejects_denied_trust():
    denied = TrustDecision(approved=False, confidence=1.0, evidence=("blocked-call:1:exec",))

    with pytest.raises(PermissionError, match="blocked-call"):
        WorkforceOrchestrator().plan(_request(), [ComputeCandidate("provider")], denied)


def test_trust_can_be_explicitly_disabled_for_non_execution_plans():
    plan = WorkforceOrchestrator().plan(
        _request(trust_required=False), [ComputeCandidate("provider", model="demo")]
    )

    assert plan.provider == "provider"
    assert plan.trust is None
