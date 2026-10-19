"""Provider-agnostic compute economics contracts for OmniAgent.

The engine consumes normalized provider candidates. GPU Cost Optimizer can
feed the same contract through an adapter without making OmniAgent depend on a
specific accelerator catalogue or vendor SDK.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Literal

Objective = Literal["cost", "latency", "balanced"]
_VALID_OBJECTIVES = {"cost", "latency", "balanced"}


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
class ComputeCandidate:
    """Normalized execution option exposed by any provider or accelerator."""

    provider: str
    model: str = ""
    estimated_cost: float = 0.0
    estimated_latency_ms: float = 0.0
    available: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.provider, str) or not self.provider.strip():
            raise ValueError("provider must be a non-empty string")
        if not isinstance(self.model, str):
            raise ValueError("model must be a string")
        if not isinstance(self.available, bool):
            raise ValueError("available must be a boolean")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a mapping")
        object.__setattr__(self, "provider", self.provider.strip())
        object.__setattr__(self, "model", self.model.strip())
        object.__setattr__(
            self, "estimated_cost", _finite_non_negative(self.estimated_cost, "estimated_cost")
        )
        object.__setattr__(
            self,
            "estimated_latency_ms",
            _finite_non_negative(self.estimated_latency_ms, "estimated_latency_ms"),
        )


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
        if objective not in _VALID_OBJECTIVES:
            raise ValueError(f"unsupported objective: {objective}")
        if budget is not None:
            budget = _finite_non_negative(budget, "budget")
        if preferred_provider is not None and not isinstance(preferred_provider, str):
            raise ValueError("preferred_provider must be a string or None")

        options = [candidate for candidate in candidates if candidate.available]
        if not options:
            raise ValueError("no available compute candidates")
        if budget is not None:
            options = [candidate for candidate in options if candidate.estimated_cost <= budget]
            if not options:
                raise ValueError("no available compute candidate is within the requested budget")

        cost_min = min(candidate.estimated_cost for candidate in options)
        latency_min = min(candidate.estimated_latency_ms for candidate in options)
        cost_span = max(candidate.estimated_cost for candidate in options) - cost_min
        latency_span = max(candidate.estimated_latency_ms for candidate in options) - latency_min

        def normalized(value: float, minimum: float, span: float) -> float:
            return 0.0 if span == 0 else (value - minimum) / span

        def key(candidate: ComputeCandidate) -> tuple[float, int, float, str, str]:
            if objective == "cost":
                primary, secondary = candidate.estimated_cost, candidate.estimated_latency_ms
            elif objective == "latency":
                primary, secondary = candidate.estimated_latency_ms, candidate.estimated_cost
            else:
                normalized_cost = normalized(candidate.estimated_cost, cost_min, cost_span)
                normalized_latency = normalized(
                    candidate.estimated_latency_ms, latency_min, latency_span
                )
                primary = 0.7 * normalized_cost + 0.3 * normalized_latency
                secondary = candidate.estimated_cost
            preferred = 0 if candidate.provider == preferred_provider else 1
            return (
                primary,
                preferred,
                secondary,
                candidate.provider.casefold(),
                candidate.model.casefold(),
            )

        return min(options, key=key)


def candidates_from_gpu_comparisons(comparisons: Iterable[Any]) -> list[ComputeCandidate]:
    """Adapt GPU Cost Optimizer comparison objects to the neutral contract."""

    candidates = []
    for comparison in comparisons:
        candidates.append(
            ComputeCandidate(
                provider="gpu",
                model=str(comparison.gpu),
                estimated_cost=comparison.estimated_cost,
                estimated_latency_ms=float(comparison.estimated_time_seconds) * 1000,
                available=bool(comparison.meets_vram),
                metadata={
                    "vram_gb": float(comparison.vram_gb),
                    "score": float(comparison.score),
                },
            )
        )
    return candidates
