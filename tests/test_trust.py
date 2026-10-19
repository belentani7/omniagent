import pytest

from omniagent.trust import SafeExecTrustAdapter, TrustDecision, require_approved


class Finding:
    def __init__(self, rule, line, detail):
        self.rule = rule
        self.line = line
        self.detail = detail


class Evaluator:
    def __init__(self, findings):
        self.findings = findings

    def evaluate(self, source):
        return self.findings


def test_safeexec_adapter_approves_clean_source():
    decision = SafeExecTrustAdapter(Evaluator([])).evaluate("value = 1")

    assert decision.approved is True
    assert decision.confidence == 1.0
    require_approved(decision)


def test_safeexec_adapter_blocks_and_explains_findings():
    decision = SafeExecTrustAdapter(Evaluator([Finding("blocked-call", 4, "os.system")])).evaluate(
        "os.system('x')"
    )

    assert decision.approved is False
    assert decision.evidence == ("blocked-call:4:os.system",)
    with pytest.raises(PermissionError, match="blocked-call:4:os.system"):
        require_approved(decision)


def test_trust_confidence_must_be_finite_and_bounded():
    with pytest.raises(ValueError, match="confidence"):
        TrustDecision(approved=True, confidence=float("nan"))
    with pytest.raises(ValueError, match="confidence"):
        TrustDecision(approved=True, confidence=1.1)


def test_non_decision_is_not_accepted_at_trust_boundary():
    with pytest.raises(TypeError, match="TrustDecision"):
        require_approved({"approved": True})


def test_policy_evaluator_must_return_a_list():
    with pytest.raises(TypeError, match="list of findings"):
        SafeExecTrustAdapter(Evaluator(None)).evaluate("print('x')")
