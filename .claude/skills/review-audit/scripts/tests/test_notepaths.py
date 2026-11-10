import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from notepaths import find_machine_paths  # noqa: E402


class AllowedText(unittest.TestCase):
    def test_repo_relative_and_prose_pass(self):
        for text in (
            "docs/caveats.md:12", "c64cast/hw/api.py", "8/sec", "A/V sync", "and/or",
            "https://github.com/kfox/c64cast/pull/817", "a1b2c3d..e4f5a6b", "origin/main..HEAD",
            "wait... then", "refs/notes/review-audit", "3.1B/7.1B", "44% of 7.1B", "~55% real",
            "reviewer:medium: 3 reviews", "1 / 2", "./scripts/x.py",
        ):
            with self.subTest(text=text):
                self.assertEqual(find_machine_paths(text), [])


class RefusedText(unittest.TestCase):
    def test_machine_paths_are_found(self):
        for text, rule in (
            ("/opt/src/x", "absolute path"),
            ("see `/tmp/x`", "absolute path"),
            ("(/Users/someone)", "absolute path"),
            ("path:/opt/x", "absolute path"),
            ("**/opt/x**", "absolute path"),
            ("port /dev/cu.usbmodem1", "absolute path"),
            ("~/.claude/x", "home-relative path"),
            ("~someone/x", "home-relative path"),
            ("$HOME/x", "home variable"),
            ("${HOME}/x", "home variable"),
            ("%USERPROFILE%\\x", "home variable"),
            ("C:\\Users\\x", "drive path"),
            ("c:/x", "drive path"),
            ("\\\\server\\share", "network path"),
            ("c64cast/../foo", "parent traversal"),
            ("../foo", "parent traversal"),
            ("a\\..\\b", "parent traversal"),
            ("up to ..", "parent traversal"),
            ("file:///etc/passwd", "file URL"),
        ):
            with self.subTest(text=text):
                self.assertIn(rule, [r for r, _ in find_machine_paths(text)])

    def test_token_names_the_offending_word(self):
        self.assertEqual(find_machine_paths("ran in /opt/x today"), [("absolute path", "/opt/x")])

    def test_a_path_on_a_later_line_is_found(self):
        self.assertTrue(find_machine_paths("first line\n/opt/x"))


if __name__ == "__main__":
    unittest.main()
