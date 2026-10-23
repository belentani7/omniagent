# PROJECT MASTER PROMPT — OmniAgent

## Real identity and source of truth
Repository: `belentani7/omniagent`. Preserve its own Git history, package, tests, CLI, docs and security policy. Its current README and executable code are the source of truth, not unrelated conversations, backups, or repositories.

OmniAgent is a Python 3.10+ **local, alpha, rules-based AI provider router**. It routes tasks across configured providers using transparent, editable rules and records local usage estimates. It is not yet a validated autonomous coding factory, a hosted agent, or a proven cheapest-model selector.

## Product vision — maximum justified potential
Evolve this product deliberately into a trustworthy, transparent AI orchestration CLI with:
- Explainable task/provider selection and safe, documented fallbacks.
- Provider adapters with compatibility checks and resilient error handling.
- Meaningful budgets with explicit distinction between estimated spend and real provider-enforced caps.
- Privacy by design: local-first defaults, protected credentials, no prompt/response telemetry by default.
- Reproducible tests, evaluations, cross-platform installability and clear onboarding.
- **Optional** unattended coding automation through the separately gated Codex Autopilot workflow. This must never imply that MetaSkill, NOIACORE, Manos Abiertas or other brands are the same product.

## Implementation priorities
1. Preserve present behavior and keep CLI + documentation coherent.
2. Improve reproducible test coverage and safety, then provider reliability.
3. Expand opt-in connectors and use budgets, quotas and approval gates.
4. Add observability and task orchestration only when actually implemented and tested.
5. Publish only working, documented capabilities; do not invent claims or traffic numbers.

## Operating boundaries
- No new GitHub repositories. Do not rename, merge, archive, delete or publish repositories.
- Respect private code, credentials, licenses, privacy, deploy configuration and existing CI.
- Never expose API keys, private user data or provider secrets.
- Do not automatically merge, deploy, change billing or alter repository visibility.
- Do not claim tests passed without running them.
- Code changes must be scoped, reviewable, tested and proposed as a pull request.

## Reusable agent instruction
Read this file, README.md, SECURITY.md, pyproject.toml and the relevant tests before editing. Confirm the real product boundaries. Select the smallest high-value improvement aligned with the vision; implement it with tests, run lint/test gates and describe exact results. If blocked or no meaningful work exists, make no change and report the reason.
