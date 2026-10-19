# Contributing to OmniAgent

## Local setup

1. Fork or clone the repository and create a focused branch.
2. Install the package and development tools:
   ```bash
   python -m pip install -e ".[dev]"
   ```
3. Run the checks before opening a pull request:
   ```bash
   python -m pytest -q
   python -m ruff check .
   python -m ruff format --check .
   python -m compileall -q omniagent tests tools
   python tools/check_web_syntax.py  # Node.js required
   ```

## Guidelines

- Keep provider calls explicit; dry-run must remain network-free.
- Never log prompts, completions, API keys, or full provider error bodies.
- Do not describe local token estimates or the saved monthly target as a billing cap.
- Add offline tests for new routing, provider, configuration, and cost behavior. Mock HTTP calls; CI must not need API credentials.
- Keep user configuration writes atomic and private on POSIX systems.
- Preserve the CLI and config compatibility where practical; document migrations when a change is not compatible.
- Keep the landing page lightweight and accessible. Do not add a runtime dependency for static pages without a clear need.

## Pull requests

- Use a concise conventional commit title.
- Explain behavioral changes and any provider/model assumptions.
- Include test output and note any provider behavior that was not tested live.
- Link relevant issues with `Fixes #123` when appropriate.
