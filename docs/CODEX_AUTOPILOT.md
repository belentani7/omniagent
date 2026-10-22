# Codex Autopilot — private opt-in setup

This is a **proposal-only coding assistant for OmniAgent**. It does not manage all Belentani repositories. It runs a short, bounded Codex task using an ephemeral GitHub-hosted Ubuntu runner each hour, when enabled, and opens **draft pull requests** after validation. It does not keep a computer or this ChatGPT session online permanently.

## One-time activation after merging the setup PR

1. In this existing repository's **Settings → Secrets and variables → Actions → Secrets**, add `OPENAI_API_KEY` as a repository secret. Create this key in the OpenAI API platform. API usage is separately billed and is not guaranteed to be covered by a ChatGPT subscription. Set spending controls in the API platform.
2. Under **Settings → Secrets and variables → Actions → Variables**, add `CODEX_AUTOPILOT_ENABLED` = `true`. The workflow is intentionally disabled until then.
3. In **Settings → Actions → General → Workflow permissions**, ensure GitHub Actions has the permissions needed to open pull requests, including **Allow GitHub Actions to create and approve pull requests** when that setting is offered. Review repository/org policy.
4. In **Actions → Codex Autopilot (opt-in)** use **Run workflow** to test. Then monitor the scheduled hourly runs at minute 17 UTC.
5. Review draft PRs and test results before manually merging them. An open `automation/codex-` PR stops additional proposals until resolved; this prevents an hourly PR flood.

## Safety model

- No hardcoded tokens, no credential files in Git, checkout with `persist-credentials: false`.
- Codex uses the official OpenAI action's restricted `drop-sudo` safety strategy and workspace-scoped editing. The GitHub write token is only provided to separate non-Codex workflow steps.
- `tools/codex_change_guard.py` rejects forbidden files and changes bigger than the pilot thresholds. Lint, formatting, compilation and tests must pass to create a PR.
- Draft PRs only. Never auto-merge, deploy, alter billing, change visibility, delete repositories or broaden to private repos automatically.
- Concurrency is limited to one run at a time and each runner has a 25-minute timeout. **This is not a monetary cap**. Check API and GitHub Actions billing. GitHub cron schedules are best effort and may be delayed.
- Pause at any time by setting `CODEX_AUTOPILOT_ENABLED` to `false` (or disabling the workflow); do not delete credentials in chat.

## Optional: run Codex on your own Linux machine

A user-authorized Linux host is required. In a terminal on that machine, run:

```bash
git clone https://github.com/belentani7/omniagent.git
cd omniagent
bash tools/bootstrap_codex_linux.sh --login
```

The private clone will require your own GitHub authentication. Alternatively, install Codex directly with `npm install -g @openai/codex` and run `codex login --device-auth` to finish ChatGPT login yourself in your browser. Do not share the verification code or credentials with the assistant.

If you want the assistant to access that Linux terminal through Desktop Commander Remote, first connect and authorize the host at https://mcp.desktopcommander.app/ . This chat currently cannot execute commands on an unconnected host. Keep the approved Remote process running. Codex CLI sign-in on a personal Linux machine is distinct from the `OPENAI_API_KEY` needed by the GitHub Actions automation.

## Extending to other repositories later

The GitHub `GITHUB_TOKEN` issued here is scoped to this repo; it cannot automatically modify all of `belentani7`. Extend carefully per repository, or use a separately authorized and narrowly scoped GitHub App / fine-grained token, with an allowlist, individual `PROJECT_MASTER_PROMPT.md` files, bounded quotas and human-reviewed PRs. Do not crawl or change unrelated repositories just because they are visible.
