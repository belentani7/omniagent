"""Provider-agnostic compute economics contracts for OmniAgent.

The engine consumes normalized provider candidates. GPU Cost Optimizer can
feed the same contract through an adapter without making OmniAgent depend on a
specific accelerator catalogue or vendor SDK.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Literal

Objective = Literal["cost", "latency", "balanced"]


@dataclass(frozen=True)
class ComputeCandidate:
    """Normalized execution option exposed by any provider or accelerator."""

    provider: str
    model: str = ""
    estimated_cost: float = 0.0
    estimated_latency_ms: float = 0.0
    available: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.estimated_cost < 0:
            raise ValueError("estimated_cost must be non-negative")
        if self.estimated_latency_ms < 0:
            raise ValueError("estimated_latency_ms must be non-negative")


class ComputeEconomicsEngine:
    """Select a provider using explicit budget and objective constraints."""

    def choose(
        self,
        candidates: Iterable[ComputeCandidate],
        *,
        budget: float | None = None,
        preferred_provider: str | None = None,
        objective: Objective = "balanced",
    ) -> ComputeCandidate:
        options = [candidate for candidate in candidates if candidate.available]
        if budget is not None:
            if budget < 0:
                raise ValueError("budget must be non-negative")
            affordable = [candidate for candidate in options if candidate.estimated_cost <= budget]
            if affordable:
                options = affordable
        if not options:
            raise ValueError("no available compute candidates")

        def key(candidate: ComputeCandidate) -> tuple[float, float, int]:
            if objective == "cost":
                primary, secondary = candidate.estimated_cost, candidate.estimated_latency_ms
            elif objective == "latency":
                primary, secondary = candidate.estimated_latency_ms, candidate.estimated_cost
            elif objective == "balanced":
                primary = candidate.estimated_cost * 0.7 + candidate.estimated_latency_ms * 0.3
                secondary = candidate.estimated_cost
            else:
                raise ValueError(f"unsupported objective: {objective}")
            preference = 0 if candidate.provider == preferred_provider else 1
            return primary, secondary, preference

        return min(options, key=key)


def candidates_from_gpu_comparisons(comparisons: Iterable[Any]) -> list[ComputeCandidate]:
    """Adapt GPU Cost Optimizer comparison objects to the neutral contract."""

    return [
        ComputeCandidate(
            provider="gpu",
            model=str(comparison.gpu),
            estimated_cost=float(comparison.estimated_cost),
            estimated_latency_ms=float(comparison.estimated_time_seconds) * 1000,
            available=bool(comparison.meets_vram),
            metadata={"vram_gb": float(comparison.vram_gb), "score": float(comparison.score)},
        )
        for comparison in comparisons
    ]
