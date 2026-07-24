"""Cost tracking for OmniAgent."""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path.home() / ".local" / "share" / "omniagent"
LOG_FILE = DATA_DIR / "usage.jsonl"

# Approximate cost per 1K tokens (input + output averaged)
MODEL_COSTS = {
    "anthropic": {"input": 0.015, "output": 0.075, "label": "Claude Opus"},
    "openai": {"input": 0.010, "output": 0.030, "label": "GPT-4.1"},
    "google": {"input": 0.005, "output": 0.015, "label": "Gemini Pro"},
    "deepseek": {"input": 0.001, "output": 0.002, "label": "DeepSeek V3"},
    "groq": {"input": 0.0005, "output": 0.001, "label": "Llama 3.3 70B"},
    "xiaomi": {"input": 0.002, "output": 0.006, "label": "MiMo V2.5"},
}


class CostTracker:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def log(self, provider: str, task_type: str, prompt: str, response: str):
        """Log a usage entry."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "task_type": task_type,
            "prompt_tokens": len(prompt.split()) * 1.3,  # rough estimate
            "response_tokens": len(response.split()) * 1.3,
            "estimated_cost": self._estimate_cost(provider, prompt, response),
        }
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _estimate_cost(self, provider: str, prompt: str, response: str) -> float:
        """Estimate cost of a request."""
        costs = MODEL_COSTS.get(provider, {"input": 0.01, "output": 0.03})
        prompt_tokens = len(prompt.split()) * 1.3
        response_tokens = len(response.split()) * 1.3
        return (prompt_tokens * costs["input"] + response_tokens * costs["output"]) / 1000

    def get_entries(self) -> list[dict]:
        """Read all logged entries."""
        if not LOG_FILE.exists():
            return []
        entries = []
        with open(LOG_FILE) as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

    def print_last(self, n: int = 10):
        """Print last N entries."""
        from rich.console import Console
        from rich.table import Table

        console = Console()
        entries = self.get_entries()[-n:]

        if not entries:
            console.print("[yellow]No usage logged yet[/yellow]")
            return

        table = Table(title=f"Last {len(entries)} Requests")
        table.add_column("Time", style="cyan")
        table.add_column("Provider", style="green")
        table.add_column("Task", style="yellow")
        table.add_column("Cost", style="red")

        for e in entries:
            time_str = e["timestamp"][:19]
            table.add_row(time_str, e["provider"], e["task_type"], f"€{e['estimated_cost']:.4f}")

        console.print(table)

    def print_summary(self):
        """Print cost summary."""
        from rich.console import Console
        from rich.table import Table

        console = Console()
        entries = self.get_entries()

        if not entries:
            console.print("[yellow]No usage logged yet[/yellow]")
            return

        by_provider = {}
        total = 0.0
        for e in entries:
            p = e["provider"]
            cost = e["estimated_cost"]
            by_provider[p] = by_provider.get(p, 0) + cost
            total += cost

        table = Table(title="Cost Summary")
        table.add_column("Provider", style="cyan")
        table.add_column("Requests", style="green")
        table.add_column("Total Cost", style="red")

        by_provider_count = {}
        for e in entries:
            p = e["provider"]
            by_provider_count[p] = by_provider_count.get(p, 0) + 1

        for provider, cost in sorted(by_provider.items(), key=lambda x: -x[1]):
            count = by_provider_count[provider]
            table.add_row(provider, str(count), f"€{cost:.4f}")

        table.add_row("[bold]TOTAL[/bold]", str(len(entries)), f"[bold]€{total:.4f}[/bold]")
        console.print(table)
