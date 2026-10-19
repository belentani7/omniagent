"""Provider-neutral planning contracts for the Belentani Autonomous Workforce."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable

from .economics import ComputeCandidate, ComputeEconomicsEngine, Objective
from .trust import TrustDecision, require_approved


class ExecutionStatus(str, Enum):
    PLANNED = "planned"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


def _finite_non_negative(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite, non-negative number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"{label} must be a finite, non-negative number") from None
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{label} must be a finite, non-negative number")
    return number


@dataclass(frozen=True)
class Evidence:
    """A traceable fact attached to a plan or result."""

    source: str
    reference: str
    detail: str

    def __post_init__(self) -> None:
        if not all(isinstance(value, str) for value in (self.source, self.reference, self.detail)):
            raise ValueError("evidence fields must be strings")
        if not self.source.strip() or not self.reference.strip():
            raise ValueError("evidence source and reference must not be empty")


@dataclass(frozen=True)
class ExecutionRequest:
    """Provider-neutral request emitted by a workforce module."""

    request_id: str
    task_type: str
    payload: dict[str, Any]
    budget: float | None = None
    objective: Objective = "balanced"
    trust_required: bool = True
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise ValueError("request_id must be a non-empty string")
        if not isinstance(self.task_type, str) or not self.task_type.strip():
            raise ValueError("task_type must be a non-empty string")
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be a mapping")
        if self.budget is not None:
            object.__setattr__(self, "budget", _finite_non_negative(self.budget, "budget"))
        if self.objective not in {"cost", "latency", "balanced"}:
            raise ValueError(f"unsupported objective: {self.objective}")
        if not isinstance(self.trust_required, bool):
            raise ValueError("trust_required must be a boolean")
        if not isinstance(self.evidence, tuple) or not all(
            isinstance(item, Evidence) for item in self.evidence
        ):
            raise ValueError("evidence must be a tuple of Evidence")
        object.__setattr__(self, "request_id", self.request_id.strip())
        object.__setattr__(self, "task_type", self.task_type.strip())


@dataclass(frozen=True)
class ExecutionPlan:
    """Explainable plan produced before any provider is called."""

    request_id: str
    provider: str
    model: str
    estimated_cost: float
    estimated_latency_ms: float
    trust: TrustDecision | None
    status: ExecutionStatus = ExecutionStatus.PLANNED
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.request_id or not self.provider or not isinstance(self.model, str):
            raise ValueError("plan requires a request ID, provider, and model string")
        object.__setattr__(
            self, "estimated_cost", _finite_non_negative(self.estimated_cost, "estimated_cost")
        )
        object.__setattr__(
            self,
            "estimated_latency_ms",
            _finite_non_negative(self.estimated_latency_ms, "estimated_latency_ms"),
        )
        if not isinstance(self.status, ExecutionStatus):
            raise ValueError("status must be an ExecutionStatus")
        if not isinstance(self.evidence, tuple) or not all(
            isinstance(item, Evidence) for item in self.evidence
        ):
            raise ValueError("evidence must be a tuple of Evidence")


@dataclass(frozen=True)
class ExecutionResult:
    """Normalized result envelope for API, CLI and Revenue OS consumers."""

    request_id: str
    status: ExecutionStatus
    provider: str
    output: Any = None
    actual_cost: float | None = None
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)
    error: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise ValueError("request_id must be a non-empty string")
        if not isinstance(self.status, ExecutionStatus):
            raise ValueError("status must be an ExecutionStatus")
        if not isinstance(self.provider, str) or not self.provider.strip():
            raise ValueError("provider must be a non-empty string")
        if self.actual_cost is not None:
            object.__setattr__(
                self, "actual_cost", _finite_non_negative(self.actual_cost, "actual_cost")
            )
        if not isinstance(self.evidence, tuple) or not all(
            isinstance(item, Evidence) for item in self.evidence
        ):
            raise ValueError("evidence must be a tuple of Evidence")
        if self.error is not None and not isinstance(self.error, str):
            raise ValueError("error must be a string or None")


class WorkforceOrchestrator:
    """Build an execution plan while enforcing the trust boundary."""

    def __init__(self, economics: ComputeEconomicsEngine | None = None) -> None:
        self.economics = economics or ComputeEconomicsEngine()

    def plan(
        self,
        request: ExecutionRequest,
        candidates: Iterable[ComputeCandidate],
        trust: TrustDecision | None = None,
    ) -> ExecutionPlan:
        if not isinstance(request, ExecutionRequest):
            raise TypeError("request must be an ExecutionRequest")
        if request.trust_required:
            if trust is None:
                raise PermissionError("trust decision required before execution")
            require_approved(trust)

        selected = self.economics.choose(
            candidates,
            budget=request.budget,
            objective=request.objective,
        )
        return ExecutionPlan(
            request_id=request.request_id,
            provider=selected.provider,
            model=selected.model,
            estimated_cost=selected.estimated_cost,
            estimated_latency_ms=selected.estimated_latency_ms,
            trust=trust,
            evidence=request.evidence,
        )
