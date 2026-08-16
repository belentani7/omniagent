"""CLI entry point for OmniAgent."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from omniagent import __version__
from omniagent.config import load_config, get_available_providers
from omniagent.router import route_task, TaskType, classify
from omniagent.cost import CostTracker

console = Console()


@click.group()
@click.version_option(__version__, prog_name="omniagent")
def main():
    """OmniAgent — One CLI to route AI tasks to the best model."""
    pass


@main.command()
@click.argument("prompt")
@click.option("--provider", "-p", help="Force a specific provider")
@click.option("--verbose", "-v", is_flag=True, help="Show routing decision")
@click.option("--dry-run", is_flag=True, help="Show which provider would be used without executing")
def run(prompt: str, provider: str | None, verbose: bool, dry_run: bool):
    """Route a prompt to the best AI provider."""
    config = load_config()
    providers = get_available_providers(config)

    if not providers:
        console.print("[red]No API keys found. Set at least one:[/red]")
        for name, env in [("groq", "GROQ_API_KEY"), ("google", "GOOGLE_API_KEY"),
                          ("openrouter", "OPENROUTER_API_KEY"), ("deepseek", "DEEPSEEK_API_KEY")]:
            console.print(f"  setx {env} your-key")
        console.print("  Or run: omniagent setup")
        raise SystemExit(1)

    if provider:
        provider_name = provider
        task_type = TaskType.GENERAL
    else:
        task_type = classify(prompt)
        provider_name = route_task(task_type, config, providers)

    if dry_run or verbose:
        table = Table(title="Routing Decision")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Prompt", prompt[:80] + ("..." if len(prompt) > 80 else ""))
        table.add_row("Task Type", task_type.value)
        table.add_row("Provider", provider_name)
        table.add_row("Budget", f"EUR {config.get('monthly_budget', 'unlimited')}/mo")
        console.print(table)

    if dry_run:
        return

    from omniagent.providers import execute

    with console.status(f"[bold green]Running on {provider_name}..."):
        result = execute(provider_name, prompt, config)

    console.print(Panel(result, title=f"Response ({provider_name})", border_style="green"))

    tracker = CostTracker()
    tracker.log(provider_name, task_type.value, prompt, result)


@main.command()
def providers_list():
    """List available providers."""
    config = load_config()
    providers = get_available_providers(config)

    table = Table(title="Available Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Best For", style="yellow")

    all_providers = {
        "groq": "Code gen, quick queries, budget",
        "google": "Research, translation, general",
        "openrouter": "Any model, quality/cost balance",
        "deepseek": "Code review, math, reasoning",
        "ollama": "Local, offline, privacy",
    }

    for name, best_for in all_providers.items():
        status = "Active" if name in providers else "No API key"
        table.add_row(name, status, best_for)

    console.print(table)


@main.command()
@click.option("--last", default=10, help="Show last N entries")
@click.option("--summary", is_flag=True, help="Show summary only")
def cost(last: int, summary: bool):
    """Show cost breakdown."""
    tracker = CostTracker()
    if summary:
        tracker.print_summary()
    else:
        tracker.print_last(last)


@main.command()
@click.option("--monthly", type=float, help="Set monthly budget")
def budget(monthly: float | None):
    """Set or view budget."""
    from omniagent.config import update_config
    if monthly:
        update_config({"monthly_budget": monthly})
        console.print(f"[green]Monthly budget set to {monthly}[/green]")
    else:
        config = load_config()
        budget_val = config.get("monthly_budget", "not set")
        console.print(f"Monthly budget: {budget_val}")


@main.command()
def setup():
    """Interactive setup wizard."""
    console.print(Panel(
        "[bold]OmniAgent Setup[/bold]\n\n"
        "Enter your API keys (press Enter to skip):\n"
        "Keys are saved to ~/.config/omniagent/config.yaml",
        title="Setup",
        border_style="blue"
    ))

    from omniagent.config import update_config

    keys = {}
    for provider in ["groq", "google", "openrouter", "deepseek"]:
        key = click.prompt(f"{provider.upper()} API key (dejar vacio si no)", default="", show_default=False)
        if key:
            keys[f"{provider}_api_key"] = key

    if keys:
        update_config(keys)
        console.print(f"\n[green]Saved {len(keys)} API keys to config[/green]")
    else:
        console.print("[yellow]No keys entered[/yellow]")


if __name__ == "__main__":
    main()
