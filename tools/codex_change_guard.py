#!/usr/bin/env python3
"""Fail closed on unreviewable or sensitive modifications from scheduled Codex runs."""

from __future__ import annotations

import pathlib
import subprocess
import sys

MAX_FILES = 12
MAX_CHANGED_LINES = 1200
MAX_UNTRACKED_BYTES = 256 * 1024
FORBIDDEN_PREFIXES = (".github/", ".git/", ".venv/", "venv/", "node_modules/")
FORBIDDEN_EXACT = {
    "PROJECT_MASTER_PROMPT.md",
    "SECURITY.md",
    ".gitmodules",
    "pyproject.toml",
    "tools/codex_change_guard.py",
}


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args])


def changed_paths() -> set[str]:
    result: set[str] = set()
    for command in (
        ("diff", "--name-only", "-z", "HEAD"),
        ("ls-files", "--others", "--exclude-standard", "-z"),
    ):
        result.update(
            entry.decode("utf-8", "surrogateescape")
            for entry in git_bytes(*command).split(b"\0")
            if entry
        )
    return result


def blocked(path: str) -> bool:
    item = pathlib.PurePosixPath(path)
    name = item.name.lower()
    return (
        path in FORBIDDEN_EXACT
        or path.startswith(FORBIDDEN_PREFIXES)
        or name.startswith(".env")
        or name.endswith((".pem", ".key", ".p12", ".pfx", ".secret"))
        or "credential" in name
        or "token" in name
        or "secret" in name
        or path.startswith("/")
        or ".." in item.parts
    )


def main() -> int:
    paths = changed_paths()
    print(f"Codex changed {len(paths)} file(s).")
    if not paths:
        return 0
    if len(paths) > MAX_FILES:
        print(f"STOP: exceeds {MAX_FILES} changed files.", file=sys.stderr)
        return 1
    denied = sorted(path for path in paths if blocked(path))
    if denied:
        print(f"STOP: forbidden paths: {denied}", file=sys.stderr)
        return 1

    # Untracked files do not appear in git diff --numstat; bound their size separately.
    untracked = [entry.decode("utf-8", "surrogateescape") for entry in git_bytes("ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if entry]
    for filename in untracked:
        candidate = pathlib.Path(filename)
        if candidate.is_symlink() or not candidate.is_file():
            print(f"STOP: untracked path is not a regular file: {filename}", file=sys.stderr)
            return 1
        if candidate.stat().st_size > MAX_UNTRACKED_BYTES:
            print(f"STOP: untracked file exceeds {MAX_UNTRACKED_BYTES} bytes: {filename}", file=sys.stderr)
            return 1

    added = removed = 0
    for line in git_bytes("diff", "--numstat", "HEAD").splitlines():
        fields = line.decode("utf-8", "replace").split("\t", 2)
        if len(fields) >= 2:
            added += int(fields[0]) if fields[0].isdigit() else 0
            removed += int(fields[1]) if fields[1].isdigit() else 0
    untracked_lines = 0
    for filename in untracked:
        with open(filename, "rb") as stream:
            untracked_lines += sum(chunk.count(b"\n") for chunk in iter(lambda: stream.read(65536), b""))
    if added + removed + untracked_lines > MAX_CHANGED_LINES:
        print("STOP: diff too large for unattended PR.", file=sys.stderr)
        return 1
    print("Change guard passed. Human review still mandatory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
