# BELENTANI // VIRTUAL AI INSTRUCTIONS

> Project briefing for agents operating in this repository.
> Creative signature used by this optional Magic layer: **belentani.eu** · **noiacore.com**.

## Project identity

OmniAgent is an alpha, local Python CLI for deterministic, editable routing across configured AI providers. It calls providers directly when the user runs `oa run`; it is not a hosted service, autonomous agent, model benchmark, or billing control. `docs/` is a lightweight project landing page. `magic/` contains optional visual and audio experiments.

## Working principles

- Preserve a real product workflow: no fake provider integrations, fabricated metrics, or interactive mockups presented as working features.
- Improve the CLI and its tests before adding decorative layers. Do not replace a useful frontend or architecture without a product reason.
- Add WebGL, procedural audio, motion, or lore only when requested or when they serve the project's purpose; they are not mandatory for every repository.
- Keep credentials out of Git. Use environment variables or the private local config flow; never print keys, prompts, or provider response bodies in logs.
- Keep dry-run network-free and provider tests offline. Do not make an unapproved live API call.
- Preserve the Magic pages as optional, self-contained experiments unless their scope is explicitly expanded.
- Do not claim readiness percentages, performance results, or external integration status without repeatable evidence.

## Verification

Before handing off Python changes, run the test suite, Ruff lint/format checks, package build, and the browser/plugin syntax checker when relevant. State clearly which external services were not tested live. Keep changes focused and avoid adding runtime dependencies without a reason.
