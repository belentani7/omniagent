import pytest

from omniagent.trust import SafeExecTrustAdapter, require_approved


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
    decision = SafeExecTrustAdapter(
        Evaluator([Finding("blocked-call", 4, "os.system")])
    ).evaluate("os.system('x')")

    assert decision.approved is False
    assert decision.evidence == ("blocked-call:4:os.system",)
    with pytest.raises(PermissionError, match="blocked-call:4:os.system"):
        require_approved(decision)
