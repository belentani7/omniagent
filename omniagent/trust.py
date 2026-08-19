"""Trust-layer contracts compatible with Safe-Exec policy evaluators."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class FindingLike(Protocol):
    rule: str
    line: int
    detail: str


class PolicyEvaluator(Protocol):
    def evaluate(self, source: str) -> list[FindingLike]: ...


@dataclass(frozen=True)
class TrustDecision:
    """Explainable decision required before executing untrusted source."""

    approved: bool
    confidence: float
    policy_version: str = "safeexec-1"
    reasons: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[str, ...] = field(default_factory=tuple)


class SafeExecTrustAdapter:
    """Adapt Safe-Exec's finding-based evaluator to a stable workforce contract."""

    def __init__(self, evaluator: PolicyEvaluator, policy_version: str = "safeexec-1") -> None:
        self.evaluator = evaluator
        self.policy_version = policy_version

    def evaluate(self, source: str) -> TrustDecision:
        findings = self.evaluator.evaluate(source)
        evidence = tuple(
            f"{finding.rule}:{finding.line}:{finding.detail}" for finding in findings
        )
        if findings:
            return TrustDecision(
                approved=False,
                confidence=1.0,
                policy_version=self.policy_version,
                reasons=("Safe-Exec policy blocked the source",),
                evidence=evidence,
            )
        return TrustDecision(
            approved=True,
            confidence=1.0,
            policy_version=self.policy_version,
            reasons=("Safe-Exec policy passed",),
        )


def require_approved(decision: TrustDecision) -> None:
    """Stop execution at the trust boundary when policy approval is absent."""

    if not decision.approved:
        evidence = "; ".join(decision.evidence) or "no evidence provided"
        raise PermissionError(f"execution rejected by trust policy: {evidence}")
