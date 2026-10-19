# Changelog

## [0.2.0] - 2026-10-17

### Added
- Current default model IDs for Groq, Gemini, OpenRouter, and DeepSeek, plus a dated USD price reference.
- Provider response metadata for reported token usage and local cost estimates.
- Spanish/Catalan lexical routing and word-boundary matching.
- A network-free `--dry-run`, hidden credential input, and clearer provider availability errors.
- Atomic private config and usage-log writes; legacy usage logs remain readable.
- Offline provider, CLI, cost, adapter, trust, and economics tests.
- A static landing page featuring output captured from the real network-free dry-run command.

### Changed
- Cost estimates are now model-specific and explicitly approximate; unknown prices remain unknown.
- The monthly EUR budget is labeled as an informational target, not an enforced spending cap.
- Economic selection rejects invalid numbers and strictly respects a supplied budget.
- CI runs the Python test/build matrix, enforces Ruff formatting, and checks browser/plugin JavaScript syntax.
- Project metadata and optional Magic guidance now match the CLI's real scope and avoid unsupported readiness claims.

### Fixed
- Google API keys are sent in a header, not a URL query string.
- Provider error messages no longer expose response bodies, request URLs, or exception details.
- Failed provider calls are not printed as successful output or added to usage history.
- Lead adapters reject invalid fees/identities and avoid copying raw search queries into evidence.
- The OpenCode magic plugin is valid JavaScript and opens its project-local page without a shell.

## [1.0.0] - 2025-10-15

### Added
- Initial repository setup with GitHub Actions workflows and project documentation.
- Issue and pull-request templates, Code of Conduct, and Security Policy.
- Dependabot and a CodeQL security workflow.
