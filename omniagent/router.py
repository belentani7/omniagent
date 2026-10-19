"""Task classification and routing engine."""

from __future__ import annotations

import re
import unicodedata
from enum import Enum


class TaskType(str, Enum):
    CODE_REVIEW = "code_review"
    CODE_GENERATION = "code_generation"
    TRANSLATION = "translation"
    MATH = "math"
    QUICK_QUERY = "quick_query"
    CREATIVE_WRITING = "creative_writing"
    DATA_ANALYSIS = "data_analysis"
    RESEARCH = "research"
    GENERAL = "general"


# Lightweight, editable lexical rules; this is not a learned classifier.
SIGNALS = {
    TaskType.CODE_REVIEW: [
        "review",
        "audit",
        "security",
        "vulnerability",
        "vulnerabilities",
        "bug",
        "refactor",
        "code smell",
        "n+1",
        "injection",
        "xss",
        "sql injection",
        "check code",
        "analyze code",
        "what's wrong",
        "fix this",
        "debug",
        "error",
        "revisar",
        "revision de codigo",
        "auditar",
        "seguridad",
        "vulnerabilidad",
        "depurar",
        "corregir codigo",
        "arreglar este codigo",
        "revisar el codigo",
    ],
    TaskType.CODE_GENERATION: [
        "build",
        "implement",
        "generate",
        "scaffold",
        "write code",
        "write a function",
        "write a script",
        "component",
        "function",
        "endpoint",
        "react",
        "nextjs",
        "python script",
        "bash script",
        "dockerfile",
        "sql query",
        "crear",
        "implementar",
        "generar",
        "componente",
        "funcion",
        "script de python",
        "endpoint rest",
    ],
    TaskType.TRANSLATION: [
        "translate",
        "traducir",
        "traduce",
        "traduire",
        "traduir",
        "tradueix",
        "übersetzen",
        "翻译",
        "to spanish",
        "to portuguese",
        "to english",
        "to french",
        "to catalan",
        "from spanish",
        "from portuguese",
        "multilingual",
        "al espanol",
        "al portugues",
        "al ingles",
        "al frances",
        "al catalan",
    ],
    TaskType.MATH: [
        "calculate",
        "solve",
        "equation",
        "formula",
        "proof",
        "theorem",
        "statistics",
        "probability",
        "derivative",
        "integral",
        "matrix",
        "optimization",
        "algorithm complexity",
        "big o",
        "combinatorics",
        "complexity",
        "calcular",
        "resolver",
        "ecuacion",
        "demostracion",
        "probabilidad",
        "derivada",
        "integral",
        "matriz",
        "optimizar",
    ],
    TaskType.CREATIVE_WRITING: [
        "write a story",
        "poem",
        "creative",
        "fiction",
        "narrative",
        "screenplay",
        "dialogue",
        "brainstorm",
        "ideate",
        "headline",
        "copywriting",
        "slogan",
        "brand voice",
        "tone",
        "escribe un cuento",
        "poema",
        "ficcion",
        "narrativa",
        "guion",
        "lluvia de ideas",
        "redacta una historia",
        "eslogan",
    ],
    TaskType.DATA_ANALYSIS: [
        "analyze data",
        "csv",
        "dataset",
        "statistics",
        "correlation",
        "regression",
        "chart",
        "graph",
        "visualization",
        "pandas",
        "spreadsheet",
        "excel",
        "dashboard",
        "metrics",
        "kpi",
        "analiza datos",
        "conjunto de datos",
        "correlacion",
        "regresion",
        "grafico",
        "hoja de calculo",
        "metricas",
        "indicadores",
    ],
    TaskType.RESEARCH: [
        "research",
        "investigate",
        "compare",
        "analyze",
        "survey",
        "literature review",
        "what are the best",
        "pros and cons",
        "market analysis",
        "competitor",
        "benchmark",
        "state of the art",
        "investiga",
        "compara",
        "revision bibliografica",
        "cuales son los mejores",
        "ventajas y desventajas",
        "analisis de mercado",
        "competidores",
        "estado del arte",
    ],
    TaskType.QUICK_QUERY: [
        "what is",
        "how do",
        "when was",
        "who is",
        "define",
        "explain simply",
        "tldr",
        "quick",
        "brief",
        "in one sentence",
        "que es",
        "como funciona",
        "cuando fue",
        "quien es",
        "define",
        "explica brevemente",
        "resumen rapido",
        "en una frase",
    ],
}


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold().replace("’", "'"))
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _contains_signal(prompt: str, signal: str) -> bool:
    words = _normalize(signal).split()
    if not words:
        return False
    phrase = r"\s+".join(re.escape(word) for word in words)
    return re.search(rf"(?<!\w){phrase}(?!\w)", prompt) is not None


def classify(prompt: str) -> TaskType:
    """Classify a prompt using token-boundary lexical rules in English, Spanish, and Catalan."""
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a string")
    prompt_normalized = _normalize(prompt)

    scores = {
        task_type: sum(_contains_signal(prompt_normalized, signal) for signal in keywords)
        for task_type, keywords in SIGNALS.items()
    }
    scores = {task_type: score for task_type, score in scores.items() if score > 0}
    if not scores:
        return TaskType.GENERAL

    # Prefer more specific classes when lexical signal counts tie.
    specificity = [
        TaskType.TRANSLATION,
        TaskType.MATH,
        TaskType.CODE_REVIEW,
        TaskType.CREATIVE_WRITING,
        TaskType.DATA_ANALYSIS,
        TaskType.RESEARCH,
        TaskType.CODE_GENERATION,
        TaskType.QUICK_QUERY,
    ]
    return max(scores, key=lambda task_type: (scores[task_type], -specificity.index(task_type)))


def route_task(task_type: TaskType, config: dict, available_providers: list[str]) -> str:
    """Route a task type to its preferred available provider, then use fallbacks."""
    routing = config.get("routing", {})
    default_provider = config.get("default_provider", "groq")
    preferred = routing.get(task_type.value, default_provider)

    if preferred in available_providers:
        return preferred

    from omniagent.config import FALLBACK_ORDER

    for provider in FALLBACK_ORDER:
        if provider in available_providers:
            return provider
    return available_providers[0] if available_providers else "none"


def route_with_economics(
    task_type: TaskType,
    config: dict,
    candidates: list[dict],
    *,
    budget: float | None = None,
    objective: str = "balanced",
) -> str:
    """Route using normalized cost/latency candidates when economics is enabled.

    Each candidate must contain ``provider`` and may contain ``model``,
    ``estimated_cost``, ``estimated_latency_ms`` and ``available``. The
    historical ``route_task`` remains the compatibility path for callers that
    only provide provider names. A requested budget is enforced strictly: no
    over-budget candidate is returned.
    """
    from omniagent.economics import ComputeCandidate, ComputeEconomicsEngine

    normalized = [ComputeCandidate(**candidate) for candidate in candidates]
    preferred = config.get("routing", {}).get(task_type.value)
    selected = ComputeEconomicsEngine().choose(
        normalized,
        budget=budget,
        preferred_provider=preferred,
        objective=objective,
    )
    return selected.provider
