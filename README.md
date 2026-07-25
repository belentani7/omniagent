# OmniAgent

**One CLI to route AI tasks to the best model.**

Stop switching between multiple AI CLIs manually. OmniAgent detects your task type, picks the optimal model for the job, and routes it automatically.

```bash
# Instead of using different tools for different tasks:
# tool-a "analyze this code"
# tool-b "translate this text"
# tool-c "write a function"

# Do this:
oa "analyze this code"      # → routes to best code analysis model
oa "translate this text"    # → routes to best multilingual model
oa "write a function"       # → routes to best code generation model
```

## Install

```bash
pip install omniagent-cli
# or
pipx install omniagent-cli
```

## Quick Start

```bash
# Set API keys for the providers you have
export PROVIDER_A_API_KEY=your-key
export PROVIDER_B_API_KEY=your-key

# Run
oa "your task here"

# See routing decisions
oa --verbose "your task here"

# Force a specific provider
oa --provider provider-name "your task here"

# List available providers
oa providers

# Show cost breakdown
oa cost
```

## How Routing Works

| Task Type | Default Provider | Why |
|-----------|-----------------|-----|
| Code review / security | provider-a | Best at code analysis |
| Code generation | provider-a / provider-b | Fast, accurate code |
| Translation | provider-c | Multilingual strength |
| Math / reasoning | provider-d | Math specialization |
| Quick queries | provider-e / provider-d | Cheapest, fastest |
| Creative writing | provider-a | Best prose |
| Data analysis | provider-f | Structured output |
| Research | provider-b + search | Balanced quality/cost |

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

# Set preferred provider for a task type
oa config set code_review provider-a
oa config set translation provider-c

# Set budget
oa config set monthly_budget 50

# Enable/disable providers
oa config disable provider-d
```

## Supported Providers

| Provider | Models | Cost Tier |
|----------|--------|-----------|
| Provider A | Model A1, A2, A3 | Frontier / Mid / Economy |
| Provider B | Model B1, B2 | Frontier / Mid |
| Provider C | Model C1, C2 | Frontier / Mid / Economy |
| Provider D | Model D1, D2 | Mid / Reasoning / Economy |
| Provider E | Model E1, E2 | Economy (fastest) |

## Roadmap

- [ ] Parallel execution (split task across providers)
- [ ] Cost comparison mode (run same task on 3 providers, compare)
- [ ] Memory persistence across sessions
- [ ] MCP server integration
- [ ] Batch processing mode
- [ ] Web UI dashboard

## License

MIT
