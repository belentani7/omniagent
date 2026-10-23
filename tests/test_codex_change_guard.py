"""Offline regression checks for Codex change-guard untracked output."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "tools" / "codex_change_guard.py"


class GuardUntrackedTests(unittest.TestCase):
    def test_untracked_large_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / "baseline.txt").write_text("baseline\n")
            subprocess.run(["git", "add", "baseline.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
            (repo / "payload.txt").write_bytes(b"x" * (256 * 1024 + 1))
            run = subprocess.run([sys.executable, str(GUARD)], cwd=repo, text=True, capture_output=True)
            self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
            self.assertIn("exceeds", run.stderr)

    def test_untracked_small_file_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / "baseline.txt").write_text("baseline\n")
            subprocess.run(["git", "add", "baseline.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
            (repo / "safe.txt").write_text("safe\n")
            run = subprocess.run([sys.executable, str(GUARD)], cwd=repo, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
