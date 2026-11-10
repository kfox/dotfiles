import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
AUDIT = SCRIPTS / "review_audit.py"
sys.path.insert(0, str(SCRIPTS))
import check_notes_push  # noqa: E402


def run(*args, cwd, check=True):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=check, timeout=60)


class PushGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.remote = self.tmp / "remote.git"
        self.repo = self.tmp / "repo"
        run("git", "init", "-q", "--bare", str(self.remote), cwd=self.tmp)
        run("git", "init", "-q", "-b", "main", str(self.repo), cwd=self.tmp)
        for key, value in (("user.name", "t"), ("user.email", "t@example.com")):
            run("git", "config", key, value, cwd=self.repo)
        (self.repo / "f.txt").write_text("x\n")
        run("git", "add", "f.txt", cwd=self.repo)
        run("git", "commit", "-q", "-m", "init", cwd=self.repo)
        run("git", "remote", "add", "origin", str(self.remote), cwd=self.repo)
        run("git", "push", "-q", "origin", "main", cwd=self.repo)
        run(sys.executable, str(AUDIT), "--repo", str(self.repo), "install-hook", cwd=self.repo)

    def note(self, text):
        run("git", "notes", "--ref=review-audit", "add", "-f", "-m", text, "HEAD", cwd=self.repo)

    def push_notes(self):
        return run("git", "push", "origin", "refs/notes/review-audit", cwd=self.repo, check=False)

    def test_clean_note_is_pushed(self):
        self.note("tokens: 3.1B total, see docs/caveats.md")
        self.assertEqual(self.push_notes().returncode, 0)

    def test_absolute_path_is_refused(self):
        self.note("scripts live in /opt/src/x")
        pushed = self.push_notes()
        self.assertNotEqual(pushed.returncode, 0)
        self.assertIn("absolute path: /opt/src/x", pushed.stderr)

    def test_traversal_is_refused(self):
        self.note("see c64cast/../foo")
        self.assertNotEqual(self.push_notes().returncode, 0)

    def test_a_path_overwritten_in_history_is_still_refused(self):
        self.note("ran in /opt/x")
        self.note("clean now")
        self.assertNotEqual(self.push_notes().returncode, 0)

    def test_a_note_already_on_the_remote_is_not_rechecked(self):
        self.note("clean")
        self.assertEqual(self.push_notes().returncode, 0)
        self.assertEqual(self.push_notes().returncode, 0)

    def test_a_tip_the_remote_already_has_passes(self):
        self.note("clean")
        tip = run("git", "rev-parse", "refs/notes/review-audit", cwd=self.repo).stdout.strip()
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.repo)
        line = f"refs/notes/review-audit {tip} refs/notes/review-audit {tip}"
        self.assertEqual(check_notes_push.violations([line]), [])

    def test_notes_pushed_to_a_branch_name_are_checked(self):
        self.note("ran in /opt/x")
        pushed = run("git", "push", "origin", "refs/notes/review-audit:refs/heads/sneaky",
                     cwd=self.repo, check=False)
        self.assertNotEqual(pushed.returncode, 0)

    def test_branch_push_skips_the_guard(self):
        hook = (self.repo / ".git" / "hooks" / "pre-push")
        hook.write_text(hook.read_text().replace("check_notes_push.py", "missing_guard.py"))
        (self.repo / "g.txt").write_text("y\n")
        run("git", "add", "g.txt", cwd=self.repo)
        run("git", "commit", "-q", "-m", "more", cwd=self.repo)
        self.assertEqual(run("git", "push", "origin", "main", cwd=self.repo, check=False).returncode, 0)

    def test_a_missing_guard_blocks_a_notes_push(self):
        hook = (self.repo / ".git" / "hooks" / "pre-push")
        hook.write_text(hook.read_text().replace("check_notes_push.py", "missing_guard.py"))
        self.note("clean")
        self.assertNotEqual(self.push_notes().returncode, 0)

    def test_an_existing_hook_is_chained(self):
        hooks = self.repo / ".git" / "hooks"
        (hooks / "pre-push").unlink()
        (hooks / "pre-push").write_text("#!/bin/sh\nexit 3\n")
        os.chmod(hooks / "pre-push", 0o755)
        run(sys.executable, str(AUDIT), "--repo", str(self.repo), "install-hook", cwd=self.repo)
        self.assertTrue((hooks / "pre-push.local").exists())
        self.note("clean")
        self.assertNotEqual(self.push_notes().returncode, 0)

    def test_reinstall_keeps_one_guard(self):
        run(sys.executable, str(AUDIT), "--repo", str(self.repo), "install-hook", cwd=self.repo)
        self.assertFalse((self.repo / ".git" / "hooks" / "pre-push.local").exists())


class NoteCommand(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        run("git", "init", "-q", "-b", "main", cwd=self.repo)
        for key, value in (("user.name", "t"), ("user.email", "t@example.com")):
            run("git", "config", key, value, cwd=self.repo)
        run("git", "commit", "-q", "--allow-empty", "-m", "init", cwd=self.repo)

    def add_note(self, text):
        draft = self.repo / "draft.md"
        draft.write_text(text)
        return run(sys.executable, str(AUDIT), "--repo", str(self.repo), "note", "--file", str(draft),
                   cwd=self.repo, check=False)

    def test_machine_path_is_refused_at_write_time(self):
        added = self.add_note("until: 2026-10-27\nran in /opt/x\n")
        self.assertNotEqual(added.returncode, 0)
        self.assertIn("absolute path", added.stderr)

    def test_unfilled_placeholder_is_refused(self):
        self.assertNotEqual(self.add_note("sample: <fill in: N real of 20>\n").returncode, 0)

    def test_clean_note_is_added_and_found_by_last(self):
        self.assertEqual(self.add_note("until: 2026-10-27\nsample: 12 real of 20\n").returncode, 0)
        latest = run(sys.executable, str(AUDIT), "--repo", str(self.repo), "last", cwd=self.repo)
        self.assertIn("next --since: 2026-10-28", latest.stdout)


if __name__ == "__main__":
    unittest.main()
