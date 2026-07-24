# OmniAgent

**One CLI to route them all.**

Stop switching between Claude, Gemini, Codex, DeepSeek, Qwen, and MiMo manually. OmniAgent detects your task type, picks the best model for the job, and routes it automatically.

```bash
# Instead of this:
claude "analyze this code for security issues"
gemini "translate this to Portuguese"
codex "write a React component"
deepseek "solve this math problem"

# Do this:
oa "analyze this code for security issues"    # → routes to Claude (best at code review)
oa "translate this to Portuguese"              # → routes to Gemini (best at multilingual)
oa "write a React component"                   # → routes to Codex (best at React)
oa "solve this math problem"                   # → routes to DeepSeek (best at math)
```

## Why

You have 5+ AI CLIs installed. Each one is good at different things. But:
- You waste time deciding which to use
- You overpay by using expensive models for cheap tasks
- You lose context switching between tools
- There's no cost tracking across providers

OmniAgent fixes this.

## Install

```bash
pip install omniagent-cli
# or
pipx install omniagent-cli
```

## Quick Start

```bash
# Set your API keys (only the ones you have)
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIza...
export OPENAI_API_KEY=sk-...

# Run
oa "your task here"

# See routing decisions
oa --verbose "your task here"

# Force a specific model
oa --model claude "your task here"

# List available models
oa models

# Show cost breakdown
oa cost
```

## How Routing Works

| Task Type | Default Model | Why |
|-----------|---------------|-----|
| Code review / security | Claude Opus | Best at code analysis |
| Code generation | Codex / Claude Sonnet | Fast, accurate code |
| Translation | Gemini Pro | Multilingual strength |
| Math / reasoning | DeepSeek R1 | Math specialization |
| Quick queries | Gemini Flash / DeepSeek V4 | Cheapest, fastest |
| Creative writing | Claude Opus | Best prose |
| Data analysis | GPT-4.1 | Structured output |
| Research | Claude Sonnet + search | Balanced quality/cost |

## Cost Tracking

```bash
# See total spend by provider
oa cost

# See per-task cost
oa cost --last 10

# Set budget alerts
oa budget --monthly 50
```

## Configuration

```bash
# List all settings
oa config

# Set preferred model for a task type
oa config set code_review claude-opus
oa config set translation gemini-pro

# Set budget
oa config set monthly_budget 50

# Enable/disable providers
oa config disable deepseek
```

## Supported Models

| Provider | Models | Cost Tier |
|----------|--------|-----------|
| Anthropic | Opus 4, Sonnet 4, Haiku 3.5 | Frontier / Mid / Economy |
| OpenAI | GPT-5.6, GPT-4.1, GPT-4.1-mini | Frontier / Mid / Economy |
| Google | Gemini 3.1 Pro, Flash, 2.0 Flash | Frontier / Mid / Economy |
| DeepSeek | V3.2, R1, V4 Flash | Mid / Reasoning / Economy |
| Xiaomi | MiMo-V2.5-Pro, V2.5-Lite | Mid / Economy |
| Groq | Llama 3.3 70B, Mixtral 8x7B | Economy (fastest) |

## Roadmap

- [ ] Parallel execution (split task across models)
- [ ] Cost comparison mode (run same task on 3 models, compare)
- [ ] Memory persistence across sessions
- [ ] MCP server integration
- [ ] Batch processing mode
- [ ] Web UI dashboard

## License

MIT

## Built by

Pedro Belentani — AI Trust & Safety Specialist, Barcelona
