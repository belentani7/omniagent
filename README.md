# OmniAgent

**A local CLI for routing AI tasks across providers with transparent, editable rules.**

OmniAgent classifies a prompt, selects a configured provider, calls that provider directly, and keeps a small local usage log. It is an **alpha, rules-based router**—not a model-quality benchmark, autonomous agent, hosted backend, or guaranteed cheapest/best-model selector.

## Quick start

Requires Python 3.10+.

```bash
python -m pip install -e .
oa --help
oa run --dry-run "translate this to Spanish"  # preview only; no network request
```

Configure credentials through environment variables or the hidden-input setup wizard:

```bash
oa setup
# Or, for example:
export GROQ_API_KEY="..."                 # bash/zsh
$env:GROQ_API_KEY="..."                   # PowerShell
oa providers-list
oa run "review this code for security issues"
```

`oa setup` stores keys in the local configuration file. On POSIX it is written atomically with owner-only file permissions (`0600`) inside a private directory (`0700`). Environment variables take precedence. Do not commit the config file.

## Commands

```bash
oa run --dry-run "write pytest tests"     # no provider call and no Ollama probe
oa run --verbose "write pytest tests"      # routing info; prompt text is not echoed
oa run --provider ollama "summarize this" # force a configured provider
oa providers-list
oa cost --last 10
oa cost --summary                         # all-time local estimates
oa budget --monthly 50                    # EUR planning reference only
```

A normal `oa run` sends the prompt to the selected third-party provider (or the configured Ollama endpoint). The dry run does not send the prompt or make a network request. When no provider is configured, a dry run still shows the preferred provider from the local rules.

## Default providers

Model IDs are defaults, not quality rankings; change them in the local config when needed. Check provider availability and pricing before use.

| Provider | Default model | Credential | Pricing notes |
|---|---|---|---|
| Groq | `openai/gpt-oss-120b` | `GROQ_API_KEY` | Hosted, paid; rates vary by usage mode |
| Google Gemini | `gemini-3.8-flash` | `GOOGLE_API_KEY` | Free and paid tiers may have different rates/limits |
| OpenRouter | `qwen/qwen3.8-27b:free` | `OPENROUTER_API_KEY` | Free endpoint; rate limits and availability apply |
| DeepSeek | `deepseek-flash` | `DEEPSEEK_API_KEY` | Peak/off-peak and cache-hit pricing vary |
| Ollama | `qwen2.5-coder:7b` | None | Local inference; hardware and electricity are not included |

Public price references are recorded in `omniagent/cost.py` as a snapshot dated **2026-10-17**. Provider terms, model IDs, prices, free-tier quotas, and output schemas can change; check the provider dashboards and documentation before use. Examples: [Groq models](https://console.groq.com/docs/models), [Gemini models](https://ai.google.dev/gemini-api/docs/models), [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing), [OpenRouter model](https://openrouter.ai/qwen/qwen3.8-27b:free), [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing/).

## Routing and configuration

The router uses deterministic keyword rules in English, Spanish, and Catalan. It is intentionally simple and explainable; it does not produce confidence scores or abstain. Unrecognized prompts use the configured default provider, while overlapping signals are resolved by a fixed priority order. Provider fallback follows the order `groq → google → deepseek → openrouter → ollama` when a preferred provider is unavailable.

Configuration is stored at:

- Linux/macOS: `$XDG_CONFIG_HOME/omniagent/config.yaml`, otherwise `~/.config/omniagent/config.yaml`.
- Windows: `%APPDATA%/omniagent/config.yaml`.

Supported settings include `routing`, `models`, `default_provider`, `max_output_tokens`, `ollama_base_url`, and `monthly_budget`. The monthly budget is a **EUR planning reference only**: OmniAgent does not block calls, reserve funds, or enforce provider billing limits.

## Usage and cost estimates

`oa cost` reads `usage.jsonl` in the local application-data directory. It stores provider/model, task type, token counts, and estimated USD cost—**not prompts or responses**. Provider-reported usage is used when available; otherwise a word-count heuristic estimates tokens. Public snapshot prices are applied only to an exact known model. Unknown model prices stay unknown, not zero.

These are estimates, not invoices or safety limits. Free-tier eligibility, peak/off-peak rates, caching, provider routing, taxes, media/tool use, and future price changes can make the actual bill different. Check the provider's own usage dashboard. The stored `monthly_budget` does not enforce a cap.

## Tests and development

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m compileall -q omniagent tests tools
python tools/check_web_syntax.py  # requires Node.js
```

The package is a local CLI, not a hosted service. `docs/` contains the lightweight static landing page and ecosystem directory used by GitHub Pages and the Vercel static project. The root `ecosistema.html` remains as a matching source copy; CI checks that it stays in sync with `docs/ecosistema.html`. `magic/` contains optional local browser experiments, not required to route a prompt.

## License

MIT. See `LICENSE`.
