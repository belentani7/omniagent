# Security Policy

## Reporting a vulnerability

Please report security vulnerabilities privately to **belentani7pedro@gmail.com**. Do not include live API keys or personal data in a public issue.

## Data and credentials

- A normal `oa run` sends the prompt to the selected provider or configured Ollama server. Review that provider's terms before sending sensitive data.
- `oa setup` hides API key input. POSIX config and usage files are written with owner-only permissions and atomic replacement. Windows uses the current user's application-data directory and inherited filesystem ACLs.
- Environment variables take precedence over saved keys.
- The usage log stores provider/model, task type, token counts, and cost estimates. It does not store prompts, completions, API keys, or full provider error bodies.
- Provider/network errors are sanitized before they are shown. Do not add request headers, secrets, or raw response bodies to logs or tests.
- `monthly_budget` is informational only. It is not a hard spend limit; set actual billing controls with the provider.

## Automated checks

The repository runs CodeQL and Gitleaks checks in GitHub Actions and uses Dependabot for Python and GitHub Actions dependencies. These checks reduce risk but do not replace review of changes, model/provider pricing, or live deployment settings.
