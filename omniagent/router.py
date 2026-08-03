"""Task classification and routing engine."""

import re
from enum import Enum


class TaskType(Enum):
    CODE_REVIEW = "code_review"
    CODE_GENERATION = "code_generation"
    TRANSLATION = "translation"
    MATH = "math"
    QUICK_QUERY = "quick_query"
    CREATIVE_WRITING = "creative_writing"
    DATA_ANALYSIS = "data_analysis"
    RESEARCH = "research"
    GENERAL = "general"


# Keywords that signal task type
SIGNALS = {
    TaskType.CODE_REVIEW: [
        "review", "audit", "security", "vulnerability", "vulnerabilities",
        "bug", "refactor", "code smell", "n+1", "injection", "xss",
        "sql injection", "check code", "analyze code", "what's wrong",
        "fix this", "debug", "error",
    ],
    TaskType.CODE_GENERATION: [
        "build", "implement", "generate", "scaffold",
        "component", "function", "endpoint", "react", "nextjs",
        "python script", "bash script", "dockerfile", "sql query",
    ],
    TaskType.TRANSLATION: [
        "translate", "traducir", "traduire", "übersetzen", "翻译",
        "to spanish", "to portuguese", "to english", "to french",
        "to catalan", "from spanish", "from portuguese", "multilingual",
    ],
    TaskType.MATH: [
        "calculate", "solve", "equation", "formula", "proof", "theorem",
        "statistics", "probability", "derivative", "integral", "matrix",
        "optimization", "algorithm complexity", "big o", "combinatorics",
        "complexity",
    ],
    TaskType.CREATIVE_WRITING: [
        "write a story", "poem", "creative", "fiction", "narrative",
        "screenplay", "dialogue", "brainstorm", "ideate", "headline",
        "copywriting", "slogan", "brand voice", "tone",
    ],
    TaskType.DATA_ANALYSIS: [
        "analyze data", "csv", "dataset", "statistics", "correlation",
        "regression", "chart", "graph", "visualization", "pandas",
        "spreadsheet", "excel", "dashboard", "metrics", "kpi",
    ],
    TaskType.RESEARCH: [
        "research", "investigate", "compare", "analyze", "survey",
        "literature review", "what are the best", " pros and cons",
        "market analysis", "competitor", "benchmark", "state of the art",
    ],
    TaskType.QUICK_QUERY: [
        "what is", "how do", "when was", "who is", "define",
        "explain simply", "tldr", "quick", "brief", "in one sentence",
    ],
}


def classify(prompt: str) -> TaskType:
    """Classify a prompt into a task type based on keyword signals."""
    prompt_lower = prompt.lower()

    scores = {}
    for task_type, keywords in SIGNALS.items():
        score = sum(1 for kw in keywords if kw in prompt_lower)
        if score > 0:
            scores[task_type] = score

    if not scores:
        return TaskType.GENERAL

    # Tie-break: more specific task types win over generic ones
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
    return max(scores, key=lambda t: (scores[t], -specificity.index(t)))


def route_task(task_type: TaskType, config: dict, available_providers: list[str]) -> str:
    """Route a task type to the best available provider."""
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
