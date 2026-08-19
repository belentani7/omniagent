import pytest

from omniagent.economics import (
    ComputeCandidate,
    ComputeEconomicsEngine,
    candidates_from_gpu_comparisons,
)
from omniagent.router import TaskType, route_with_economics


def test_choose_respects_budget_and_preference():
    candidates = [
        ComputeCandidate("groq", estimated_cost=0.01, estimated_latency_ms=80),
        ComputeCandidate("deepseek", estimated_cost=0.02, estimated_latency_ms=40),
    ]

    selected = ComputeEconomicsEngine().choose(
        candidates, budget=0.02, preferred_provider="deepseek", objective="latency"
    )

    assert selected.provider == "deepseek"


def test_unavailable_candidate_is_excluded():
    candidates = [
        ComputeCandidate("gpu", model="too-small", available=False),
        ComputeCandidate("gpu", model="a100", estimated_cost=0.20),
    ]

    assert ComputeEconomicsEngine().choose(candidates).model == "a100"


def test_negative_cost_is_rejected():
    with pytest.raises(ValueError):
        ComputeCandidate("provider", estimated_cost=-1)


def test_route_with_economics_returns_provider():
    config = {"routing": {"math": "deepseek"}}
    candidates = [
        {"provider": "groq", "estimated_cost": 0.01, "estimated_latency_ms": 30},
        {"provider": "deepseek", "estimated_cost": 0.02, "estimated_latency_ms": 10},
    ]

    assert route_with_economics(TaskType.MATH, config, candidates, objective="latency") == "deepseek"


def test_gpu_comparisons_adapt_to_neutral_contract():
    class Comparison:
        gpu = "a100"
        estimated_cost = 0.03
        estimated_time_seconds = 2.5
        meets_vram = True
        vram_gb = 40
        score = 0.03

    candidate = candidates_from_gpu_comparisons([Comparison()])[0]

    assert candidate.provider == "gpu"
    assert candidate.model == "a100"
    assert candidate.estimated_latency_ms == 2500
