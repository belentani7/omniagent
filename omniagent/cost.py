"""Private local usage log with explicitly approximate USD cost estimates."""

from __future__ import annotations

import json
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from omniagent.providers import ProviderResponse


def _user_directory(environment_variable: str, fallback: Path) -> Path:
    """Use an absolute user-data directory override; ignore empty or relative values."""
    value = os.environ.get(environment_variable)
    if not value or not value.strip():
        return fallback
    candidate = Path(value).expanduser()
    return candidate if candidate.is_absolute() else fallback


if os.name == "nt":
    _DATA_ROOT = _user_directory("LOCALAPPDATA", Path.home() / "AppData" / "Local")
else:
    _DATA_ROOT = _user_directory("XDG_DATA_HOME", Path.home() / ".local" / "share")
DATA_DIR = _DATA_ROOT / "omniagent"
LOG_FILE = DATA_DIR / "usage.jsonl"

PRICING_AS_OF = "2026-10-17"

# Rates are USD per million tokens. This is a dated reference snapshot, not billing data.
MODEL_PRICING: dict[str, dict[str, Any]] = {
    "openai/gpt-oss-120b": {
        "provider": "groq",
        "input_per_million_usd": 0.15,
        "output_per_million_usd": 0.60,
        "note": "Groq public standard rates; usage modes may differ.",
    },
    "gemini-3.8-flash": {
        "provider": "google",
        "input_per_million_usd": 0.75,
        "output_per_million_usd": 3.75,
        "note": "Paid standard rates through 2026-12-31; eligible free-tier use may cost $0.",
    },
    "qwen/qwen3.8-27b:free": {
        "provider": "openrouter",
        "input_per_million_usd": 0.0,
        "output_per_million_usd": 0.0,
        "note": "Free endpoint; rate limits and availability apply.",
    },
    "deepseek-flash": {
        "provider": "deepseek",
        "input_per_million_usd": 0.30,
        "output_per_million_usd": 1.20,
        "note": "Peak cache-miss input and peak output rates; cache hits/off-peak can be lower.",
    },
    "qwen2.5-coder:7b": {
        "provider": "ollama",
        "input_per_million_usd": 0.0,
        "output_per_million_usd": 0.0,
        "note": "No provider token charge; excludes local hardware and electricity.",
    },
}


def _rough_token_count(text: str) -> int:
    """A conservative word-count fallback, not a provider tokenizer."""
    if not text:
        return 0
    return max(1, math.ceil(len(text.split()) * 1.3))


def _finite_token_count(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 1_000_000_000_000:
        return None
    return value


class CostTracker:
    """Append minimal usage metadata locally; never store prompts or responses."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
        if DATA_DIR.is_symlink():
            raise OSError(f"refusing to use symbolic-link usage data directory: {DATA_DIR}")
        if os.name != "nt":
            DATA_DIR.chmod(0o700)
            if LOG_FILE.exists() and not LOG_FILE.is_symlink():
                LOG_FILE.chmod(0o600)

    @staticmethod
    def _estimate_cost(
        provider: str,
        model: str,
        prompt_tokens: int,
        response_tokens: int,
    ) -> float | None:
        pricing = MODEL_PRICING.get(model)
        if not pricing or pricing["provider"] != provider:
            return None
        try:
            cost = (
                prompt_tokens * pricing["input_per_million_usd"]
                + response_tokens * pricing["output_per_million_usd"]
            ) / 1_000_000
        except (OverflowError, TypeError):
            return None
        return cost if math.isfinite(cost) and cost >= 0 else None

    def log(
        self, provider: str, task_type: str, prompt: str, response: ProviderResponse
    ) -> dict[str, Any]:
        """Log usage without retaining either prompt or generated text."""
        if not isinstance(response, ProviderResponse):
            raise TypeError("response must be a ProviderResponse")
        if not isinstance(prompt, str):
            raise TypeError("prompt must be a string")

        input_tokens = _finite_token_count(response.input_tokens)
        output_tokens = _finite_token_count(response.output_tokens)
        if input_tokens is None:
            input_tokens = _rough_token_count(prompt)
        if output_tokens is None:
            output_tokens = _rough_token_count(response.text)
        if response.input_tokens is not None and response.output_tokens is not None:
            usage_source = "provider"
        elif response.input_tokens is not None or response.output_tokens is not None:
            usage_source = "mixed_provider_and_word_count_estimate"
        else:
            usage_source = "word_count_heuristic"

        estimated_cost = self._estimate_cost(provider, response.model, input_tokens, output_tokens)
        pricing = MODEL_PRICING.get(response.model)
        pricing_note = (
            pricing["note"]
            if pricing and pricing["provider"] == provider
            else "No matching model price snapshot."
        )
        entry = {
            "schema_version": 2,
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "provider": provider,
            "model": response.model,
            "task_type": task_type,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "usage_source": usage_source,
            "estimated_cost_usd": estimated_cost,
            "pricing_as_of": PRICING_AS_OF if estimated_cost is not None else None,
            "pricing_note": pricing_note,
        }
        _append_private_jsonl(LOG_FILE, entry)
        return entry

    def get_entries(self) -> list[dict[str, Any]]:
        """Read the local log and normalize entries written by the 0.1 series."""
        if not LOG_FILE.exists():
            return []
        if LOG_FILE.is_symlink():
            raise OSError(f"refusing to read usage log symbolic link: {LOG_FILE}")

        entries: list[dict[str, Any]] = []
        with LOG_FILE.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"usage log is invalid JSON on line {line_number}: {LOG_FILE}"
                    ) from exc
                if not isinstance(entry, dict):
                    raise ValueError(f"usage log line {line_number} must be a JSON object")
                entries.append(_normalize_entry(entry))
        return entries

    def month_summary(self, month: str) -> dict[str, Any]:
        """Return local estimates for one YYYY-MM month, without claiming provider billing."""
        import re

        if not isinstance(month, str) or re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])", month) is None:
            raise ValueError("month must be YYYY-MM (01 through 12)")
        entries = [
            entry for entry in self.get_entries()
            if str(entry.get("timestamp", "")).startswith(month + "-")
        ]
        known_total = 0.0
        unknown_count = 0
        for entry in entries:
            amount = _non_negative_finite_float(entry.get("estimated_cost_usd"))
            if amount is None:
                unknown_count += 1
            else:
                known_total += amount
        return {
            "month": month,
            "requests": len(entries),
            "known_estimate_usd": known_total,
            "unknown_price_requests": unknown_count,
        }

    def print_month(self, month: str) -> None:
        """Present the current month's *known* estimates and missing-price warning."""
        from rich.console import Console
        from rich.table import Table

        summary = self.month_summary(month)
        table = Table(title=f"Usage estimates for {month}")
        table.add_column("Metric")
        table.add_column("Value")
        table.add_row("Requests", str(summary["requests"]))
        table.add_row("Known USD estimate", f'${summary["known_estimate_usd"]:.6f}')
        table.add_row("Unknown-price requests", str(summary["unknown_price_requests"]))
        console = Console()
        console.print(table)
        _print_estimate_disclaimer(console)

    def print_last(self, n: int = 10) -> None:
        from rich.console import Console
        from rich.table import Table

        if isinstance(n, bool) or not isinstance(n, int) or n < 1:
            raise ValueError("n must be a positive integer")
        console = Console()
        entries = self.get_entries()[-n:]
        if not entries:
            console.print("[yellow]No usage logged yet[/yellow]")
            return

        table = Table(title=f"Last {len(entries)} Requests")
        table.add_column("Time", style="cyan")
        table.add_column("Provider", style="green")
        table.add_column("Model", style="blue")
        table.add_column("Input / output tokens", style="yellow")
        table.add_column("Estimated USD", style="red")
        for entry in entries:
            amount = _format_cost(entry.get("estimated_cost_usd"))
            table.add_row(
                str(entry.get("timestamp", "unknown"))[:19],
                str(entry.get("provider", "unknown")),
                str(entry.get("model", "unknown")),
                f"{entry.get('input_tokens', '?')} / {entry.get('output_tokens', '?')}",
                amount,
            )
        console.print(table)
        _print_estimate_disclaimer(console)

    def print_summary(self) -> None:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        entries = self.get_entries()
        if not entries:
            console.print("[yellow]No usage logged yet[/yellow]")
            return

        totals: dict[str, float] = {}
        counts: dict[str, int] = {}
        unknown: dict[str, int] = {}
        for entry in entries:
            provider = str(entry.get("provider", "unknown"))
            counts[provider] = counts.get(provider, 0) + 1
            amount = entry.get("estimated_cost_usd")
            if amount is None:
                unknown[provider] = unknown.get(provider, 0) + 1
            else:
                totals[provider] = totals.get(provider, 0.0) + amount

        table = Table(title="All-time Usage Summary")
        table.add_column("Provider", style="cyan")
        table.add_column("Requests", style="green")
        table.add_column("Estimated USD", style="red")
        table.add_column("Unknown-price requests", style="yellow")
        for provider in sorted(counts, key=lambda name: (-totals.get(name, 0.0), name)):
            table.add_row(
                provider,
                str(counts[provider]),
                f"${totals[provider]:.6f}" if provider in totals else "unknown",
                str(unknown.get(provider, 0)),
            )
        total_known = sum(totals.values())
        table.add_row(
            "TOTAL",
            str(len(entries)),
            f"${total_known:.6f} known estimates",
            str(sum(unknown.values())),
        )
        console.print(table)
        _print_estimate_disclaimer(console)


def _append_private_jsonl(path: Path, entry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != "nt":
        path.parent.chmod(0o700)
    if path.is_symlink():
        raise OSError(f"refusing to append to usage log symbolic link: {path}")

    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        if os.name != "nt":
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "a", encoding="utf-8", newline="\n") as stream:
            descriptor = -1
            stream.write(json.dumps(entry, ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _normalize_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Validate display fields and retain compatibility with legacy usage logs."""
    normalized = dict(entry)
    if "estimated_cost_usd" not in normalized and "estimated_cost" in normalized:
        normalized["estimated_cost_usd"] = _non_negative_finite_float(
            normalized.get("estimated_cost")
        )
        normalized.setdefault(
            "pricing_note", "Legacy 0.1 estimate; historical rates were not versioned."
        )
    for field in ("input_tokens", "output_tokens"):
        if field not in normalized:
            legacy_field = "prompt_tokens" if field == "input_tokens" else "response_tokens"
            value = _non_negative_finite_float(normalized.get(legacy_field))
            normalized[field] = max(0, math.ceil(value)) if value is not None else "?"
        elif _finite_token_count(normalized[field]) is None:
            normalized[field] = "?"
    amount = normalized.get("estimated_cost_usd")
    if amount is not None:
        normalized["estimated_cost_usd"] = _non_negative_finite_float(amount)
    return normalized


def _non_negative_finite_float(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) and number >= 0 else None


def _format_cost(value: Any) -> str:
    number = _non_negative_finite_float(value)
    return "unknown" if number is None else f"${number:.6f}"


def _print_estimate_disclaimer(console: Any) -> None:
    console.print(
        "[dim]Estimates only—not a bill or spend cap. Provider-reported token counts are used when available; "
        f"prices are a public snapshot dated {PRICING_AS_OF}. Check your provider dashboard.[/dim]"
    )
