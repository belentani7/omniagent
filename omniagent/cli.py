"""CLI entry point for OmniAgent."""

from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from omniagent import __version__
from omniagent.config import (
    API_KEY_PROVIDERS,
    PROVIDER_NAMES,
    get_available_providers,
    load_config,
    update_config,
)
from omniagent.cost import CostTracker
from omniagent.providers import PROVIDER_INFO, ProviderError, execute
from omniagent.router import classify, route_task

console = Console()


@click.group()
@click.version_option(__version__, prog_name="omniagent")
def main() -> None:
    """OmniAgent — one local CLI for rule-based AI task routing."""


@main.command()
@click.argument("prompt")
@click.option("--provider", "-p", help="Force a provider instead of using the task routing rules")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show the routing decision without echoing the prompt"
)
@click.option(
    "--dry-run", is_flag=True, help="Preview routing; no provider request or network probe is made"
)
def run(prompt: str, provider: str | None, verbose: bool, dry_run: bool) -> None:
    """Route a prompt to a configured AI provider."""
    if not prompt.strip():
        raise click.BadParameter("prompt must not be empty")
    if provider is not None and provider not in PROVIDER_INFO:
        raise click.BadParameter(
            f"unknown provider; choose one of: {', '.join(PROVIDER_NAMES)}", param_hint="--provider"
        )

    try:
        config = load_config()
    except ValueError as exc:
        raise click.ClickException(str(exc)) from None

    available = get_available_providers(config, probe_ollama=not dry_run)
    task_type = classify(prompt)
    if provider:
        provider_name = provider
    elif available:
        provider_name = route_task(task_type, config, available)
    else:
        provider_name = config.get("routing", {}).get(
            task_type.value, config.get("default_provider", "groq")
        )

    if not dry_run:
        if not available:
            raise click.ClickException(
                "No provider is available. Configure an API key, or start the local Ollama server."
            )
        if provider_name not in available:
            if provider_name == "ollama":
                raise click.ClickException(
                    "Ollama is not reachable; start the local server and try again."
                )
            env_var = API_KEY_PROVIDERS.get(provider_name, f"{provider_name.upper()}_API_KEY")
            raise click.ClickException(
                f"{provider_name} is not configured; set {env_var} or run `oa setup`."
            )

    if dry_run or verbose:
        table = Table(title="Routing Preview" if dry_run else "Routing Decision")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Task type", task_type.value)
        table.add_row("Provider", provider_name)
        table.add_row(
            "Availability",
            "ready" if provider_name in available else "not checked / not configured",
        )
        table.add_row("Prompt", f"not displayed ({len(prompt)} characters)")
        budget = config.get("monthly_budget")
        budget_text = "not set" if budget is None else f"EUR {budget:,.2f}/month (reference only)"
        table.add_row("Monthly target", budget_text)
        console.print(table)
        if dry_run:
            console.print(
                "[dim]No prompt was sent. Dry-run does not call providers or probe Ollama.[/dim]"
            )
            return

    try:
        with console.status(f"[bold green]Running on {provider_name}..."):
            response = execute(provider_name, prompt, config)
    except ProviderError as exc:
        raise click.ClickException(str(exc)) from None

    # Treat provider text as plain text, never Rich markup.
    console.print(
        Panel(Text(response.text), title=f"Response ({provider_name})", border_style="green")
    )
    try:
        CostTracker().log(provider_name, task_type.value, prompt, response)
    except OSError as exc:
        console.print(
            f"[yellow]Response completed, but local usage metadata could not be saved ({type(exc).__name__}).[/yellow]"
        )


@main.command(name="providers-list")
def providers_list() -> None:
    """List available providers and the reason a provider is unavailable."""
    try:
        config = load_config()
    except ValueError as exc:
        raise click.ClickException(str(exc)) from None
    providers = get_available_providers(config)

    table = Table(title="Provider Status")
    table.add_column("Provider", style="cyan")
    table.add_column("Model", style="blue")
    table.add_column("Status", style="green")
    table.add_column("Use case", style="yellow")
    for name, details in PROVIDER_INFO.items():
        if name in providers:
            status = "Available"
        elif name == "ollama":
            status = "Local server not detected"
        else:
            status = f"Missing {API_KEY_PROVIDERS[name]}"
        table.add_row(
            name, config.get("models", {}).get(name, details["model"]), status, details["best_for"]
        )
    console.print(table)


@main.command()
@click.option(
    "--last", default=10, type=click.IntRange(min=1, max=1000), help="Show last N entries"
)
@click.option("--summary", is_flag=True, help="Show all-time totals by provider")
def cost(last: int, summary: bool) -> None:
    """Show local USD usage estimates; they are not provider invoices."""
    try:
        tracker = CostTracker()
        tracker.print_summary() if summary else tracker.print_last(last)
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from None


@main.command()
@click.option(
    "--monthly",
    type=click.FloatRange(min=0),
    help="Set a monthly planning reference in EUR (not an enforced spend cap)",
)
def budget(monthly: float | None) -> None:
    """Set or view an informational monthly budget target in EUR."""
    if monthly is not None:
        try:
            update_config({"monthly_budget": monthly})
        except (OSError, ValueError) as exc:
            raise click.ClickException(str(exc)) from None
        console.print(f"Monthly planning target set to EUR {monthly:,.2f}.")
    else:
        try:
            config = load_config()
        except ValueError as exc:
            raise click.ClickException(str(exc)) from None
        value = config.get("monthly_budget")
        console.print(
            "Monthly planning target: not set."
            if value is None
            else f"Monthly planning target: EUR {value:,.2f}."
        )
    console.print(
        "[yellow]This is a reference only. OmniAgent does not block requests or enforce provider billing limits.[/yellow]"
    )


@main.command()
def setup() -> None:
    """Save provider API keys in the private local configuration file."""
    console.print(
        Panel(
            "Enter API keys (press Enter to skip). Input is hidden.\n"
            "Keys are stored in the local OmniAgent config with owner-only permissions on POSIX.",
            title="OmniAgent Setup",
            border_style="blue",
        )
    )
    keys = {}
    for provider, env_var in API_KEY_PROVIDERS.items():
        key = click.prompt(
            f"{provider.upper()} API key (leave blank to skip)",
            default="",
            show_default=False,
            hide_input=True,
        )
        if key.strip():
            keys[f"{provider}_api_key"] = key.strip()

    if keys:
        try:
            update_config(keys)
        except (OSError, ValueError) as exc:
            raise click.ClickException(str(exc)) from None
        console.print(
            f"\n[green]Saved {len(keys)} API key(s); their values were not displayed.[/green]"
        )
    else:
        console.print("[yellow]No keys entered.[/yellow]")


if __name__ == "__main__":
    main()
