#!/usr/bin/env bash
# Install Codex CLI on an authorized Linux machine. Sign-in stays interactive.
set -euo pipefail
if ! command -v npm >/dev/null 2>&1; then
  echo "Node.js/npm are required. Install them from your trusted distribution source." >&2
  exit 1
fi
npm install -g @openai/codex
codex --version
printf '\nCodex installed. To authenticate, run:\n  codex login --device-auth\n'
if [[ "${1:-}" == "--login" ]]; then
  codex login --device-auth
fi
