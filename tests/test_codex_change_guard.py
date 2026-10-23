"""Offline regression checks for Codex change-guard untracked output."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "tools" / "codex_change_guard.py"


def make_repo(repo):
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "baseline.txt").write_text("baseline\n")
    subprocess.run(["git", "add", "baseline.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)


class GuardUntrackedTests(unittest.TestCase):
    def test_untracked_large_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            make_repo(repo)
            (repo / "payload.txt").write_bytes(b"x" * (256 * 1024 + 1))
            run = subprocess.run([sys.executable, str(GUARD)], cwd=repo, text=True, capture_output=True)
            self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
            self.assertIn("exceeds", run.stderr)

    def test_untracked_small_file_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            make_repo(repo)
            (repo / "safe.txt").write_text("safe\n")
            run = subprocess.run([sys.executable, str(GUARD)], cwd=repo, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_forbidden_rename_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            make_repo(repo)
            (repo / ".github").mkdir()
            (repo / ".github" / "ci.yml").write_text("name: test\n")
            subprocess.run(["git", "add", ".github/ci.yml"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "add workflow"], cwd=repo, check=True)
            subprocess.run(["git", "mv", ".github/ci.yml", "safe.yml"], cwd=repo, check=True)
            run = subprocess.run([sys.executable, str(GUARD)], cwd=repo, text=True, capture_output=True)
            self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
            self.assertIn(".github/ci.yml", run.stderr)

    def test_modified_tracked_binary_is_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            make_repo(repo)
            (repo / "safe.bin").write_bytes(b"x")
            subprocess.run(["git", "add", "safe.bin"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "add binary"], cwd=repo, check=True)
            (repo / "safe.bin").write_bytes(b"x" * (256 * 1024 + 1))
            run = subprocess.run([sys.executable, str(GUARD)], cwd=repo, text=True, capture_output=True)
            self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
            self.assertIn("exceeds", run.stderr)

    def test_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            make_repo(repo)
            try:
                (repo / "link.txt").symlink_to("baseline.txt")
            except (OSError, NotImplementedError):
                self.skipTest("symlink unavailable")
            run = subprocess.run([sys.executable, str(GUARD)], cwd=repo, text=True, capture_output=True)
            self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
            self.assertIn("symbolic link", run.stderr)


if __name__ == "__main__":
    unittest.main()
