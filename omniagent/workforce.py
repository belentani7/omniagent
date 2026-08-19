"""Common execution contracts for the Belentani Autonomous Workforce."""

from __future__ import annotations

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


@dataclass(frozen=True)
class Evidence:
    """A traceable fact attached to a plan or result."""

    source: str
    reference: str
    detail: str


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
