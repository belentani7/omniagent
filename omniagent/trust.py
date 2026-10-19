"""Trust-layer contracts compatible with Safe-Exec policy evaluators."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Protocol


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

    def __post_init__(self) -> None:
        if not isinstance(self.approved, bool):
            raise ValueError("approved must be a boolean")
        if isinstance(self.confidence, bool):
            raise ValueError("confidence must be a finite number from 0 to 1")
        try:
            confidence = float(self.confidence)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("confidence must be a finite number from 0 to 1") from None
        if not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("confidence must be a finite number from 0 to 1")
        if not isinstance(self.policy_version, str) or not self.policy_version.strip():
            raise ValueError("policy_version must be a non-empty string")
        if not isinstance(self.reasons, tuple) or not all(
            isinstance(item, str) for item in self.reasons
        ):
            raise ValueError("reasons must be a tuple of strings")
        if not isinstance(self.evidence, tuple) or not all(
            isinstance(item, str) for item in self.evidence
        ):
            raise ValueError("evidence must be a tuple of strings")
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "policy_version", self.policy_version.strip())


class SafeExecTrustAdapter:
    """Adapt Safe-Exec's finding-based evaluator to a stable workforce contract."""

    def __init__(self, evaluator: PolicyEvaluator, policy_version: str = "safeexec-1") -> None:
        self.evaluator = evaluator
        self.policy_version = policy_version

    def evaluate(self, source: str) -> TrustDecision:
        if not isinstance(source, str):
            raise TypeError("source must be a string")
        findings = self.evaluator.evaluate(source)
        if not isinstance(findings, list):
            raise TypeError("policy evaluator must return a list of findings")
        evidence = tuple(f"{finding.rule}:{finding.line}:{finding.detail}" for finding in findings)
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
    if not isinstance(decision, TrustDecision):
        raise TypeError("decision must be a TrustDecision")
    if not decision.approved:
        evidence = "; ".join(decision.evidence) or "no evidence provided"
        raise PermissionError(f"execution rejected by trust policy: {evidence}")
