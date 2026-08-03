# OmniAgent

**One CLI to route AI tasks to the best model.**

Stop switching between multiple AI CLIs manually. OmniAgent detects your task type, picks the optimal model for the job, and routes it automatically.

```bash
# Instead of using different tools for different tasks:
# tool-a "analyze this code"
# tool-b "translate this text"
# tool-c "write a function"

# Do this:
oa "review this code for security issues"   # → routes to DeepSeek (code review)
oa "translate this to Spanish"              # → routes to Groq (translation)
oa "write a component"                      # → routes to Groq (code generation)
oa "solve this equation"                    # → routes to DeepSeek (math)
```

## Install

```bash
pip install -e .
# or
pipx install .
```

Requires Python 3.10+. The `oa` command is available after install.

## Quick Start

```bash
# Set API keys for the providers you have
$env:GROQ_API_KEY="your-key"          # PowerShell
export GROQ_API_KEY="your-key"        # bash

# Or store keys persistently via the setup wizard
oa setup

# Run
oa "your task here"

# See routing decisions
oa run --verbose "your task here"

# Force a specific provider
oa run --provider groq "your task here"

# Preview routing without executing
oa run --dry-run "your task here"

# List available providers
oa providers-list

# Show cost breakdown
oa cost
```

## Supported Providers

| Provider   | Model                          | Cost Tier  | Best For                    |
|------------|--------------------------------|------------|-----------------------------|
| Groq       | llama-3.3-70b-versatile        | economy    | Code gen, quick, budget     |
| Google     | gemini-2.0-flash               | free       | Research, general           |
| OpenRouter | qwen-2.5-coder-32b-instruct    | variable   | Quality/cost balance        |
| DeepSeek   | deepseek-chat                  | economy    | Code review, math, reasoning|
| Ollama     | qwen2.5-coder:7b (local)       | free-local | Offline, privacy            |

API keys are read from environment variables (`GROQ_API_KEY`, `GOOGLE_API_KEY`, `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`) or from `~/.config/omniagent/config.yaml`. Ollama needs no key — just a running local server at `http://localhost:11434`.

## How Routing Works

OmniAgent classifies the prompt into a task type (code review, code generation, translation, math, quick query, creative writing, data analysis, research, general) using keyword signals. Each task type maps to a preferred provider; if that provider is unavailable, it falls back through an ordered list.

| Task Type        | Preferred Provider |
|------------------|--------------------|
| Code review      | deepseek           |
| Code generation  | groq               |
| Translation      | groq               |
| Math             | deepseek           |
| Quick query      | groq               |
| Creative writing | openrouter         |
| Data analysis    | google             |
| Research         | google             |
| General          | groq               |

Fallback order: `groq → google → deepseek → openrouter → ollama`.

## Cost Tracking

```bash
oa cost                # last 10 requests
oa cost --last 20      # custom window
oa cost --summary      # totals per provider
oa budget              # show monthly budget
oa budget --monthly 50 # set budget
```

## Configuration

Stored at `~/.config/omniagent/config.yaml`. Key options:

| Option                 | Description                                  |
|------------------------|----------------------------------------------|
| `monthly_budget`       | Monthly spending cap (EUR)                   |
| `routing.<task_type>`  | Preferred provider per task type             |
| `models.<provider>`    | Override the model per provider              |
| `ollama_base_url`      | Ollama server URL (default localhost:11434)  |

## Tests

```bash
python -m pytest tests -q
```

## Roadmap

- [ ] Parallel execution (split task across providers)
- [ ] Cost comparison mode (run same task on 3 providers, compare)
- [ ] Memory persistence across sessions
- [ ] MCP server integration
- [ ] Batch processing mode
- [ ] Web UI dashboard

## License

MIT
