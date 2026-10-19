#!/usr/bin/env python3
"""Check standalone and inline JavaScript syntax with the installed Node.js."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_TAG = re.compile(
    r"<script\b(?![^>]*\bsrc\s*=)[^>]*>(.*?)</script\s*>", re.IGNORECASE | re.DOTALL
)


def check_source(node: str, label: str, source: str) -> bool:
    result = subprocess.run(
        [node, "--input-type=module", "--check"],
        input=source,
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT,
    )
    if result.returncode:
        print(f"FAIL {label}", file=sys.stderr)
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)
        return False
    print(f"OK {label}")
    return True


def main() -> int:
    node = shutil.which("node")
    if node is None:
        print("Node.js is required to check browser/plugin scripts.", file=sys.stderr)
        return 2

    ok = True
    root_ecosystem_page = ROOT / "ecosistema.html"
    published_ecosystem_page = ROOT / "docs/ecosistema.html"
    if not root_ecosystem_page.is_file() or not published_ecosystem_page.is_file():
        print("FAIL ecosystem page copy is missing", file=sys.stderr)
        ok = False
    elif root_ecosystem_page.read_bytes() != published_ecosystem_page.read_bytes():
        print("FAIL docs/ecosistema.html is out of sync with ecosistema.html", file=sys.stderr)
        ok = False
    else:
        print("OK ecosystem page copies match")

    for relative in (Path("docs/site.js"), Path("magic/plugin.js")):
        path = ROOT / relative
        if not path.is_file():
            print(f"FAIL missing {relative}", file=sys.stderr)
            ok = False
            continue
        ok = check_source(node, relative.as_posix(), path.read_text(encoding="utf-8")) and ok

    for path in sorted((ROOT / "magic").glob("*.html")):
        html = path.read_text(encoding="utf-8")
        for number, match in enumerate(SCRIPT_TAG.finditer(html), start=1):
            ok = (
                check_source(
                    node,
                    f"{path.relative_to(ROOT).as_posix()} inline script {number}",
                    match.group(1),
                )
                and ok
            )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
