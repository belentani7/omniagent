import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_web_syntax_script() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_web_syntax.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_hero_js_syntax_and_accessibility_guards() -> None:
    hero_js = (ROOT / "hero.js").read_text(encoding="utf-8")
    assert "visibilitychange" in hero_js
    assert "prefers-reduced-motion" in hero_js

    node = shutil.which("node")
    if node:
        result = subprocess.run(
            [node, "--check", str(ROOT / "hero.js")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
