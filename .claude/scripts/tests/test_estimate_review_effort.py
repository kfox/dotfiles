import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "estimate_review_effort.py"
PINS = "# Project\n\n## High-risk paths\n\n- `auth/**` — tokens and sessions\n\n## Commands\n\n- `make` — build\n"


def run(*args, cwd, check=True, env=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=check, timeout=60, env=env)


def lines(n, tag="x"):
    return "".join(f"{tag}{i}\n" for i in range(n))


class Repo:
    def __init__(self, root):
        self.path = root
        run("git", "init", "-q", "-b", "main", str(root), cwd=root.parent)
        for key, value in (("user.name", "t"), ("user.email", "t@example.com")):
            run("git", "config", key, value, cwd=root)

    def write(self, name, text):
        path = self.path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, message="c", **files):
        for name, text in files.items():
            self.write(name.replace("__", "/"), text)
        run("git", "add", "-A", cwd=self.path)
        run("git", "commit", "-q", "--allow-empty", "-m", message, cwd=self.path)
        return self.head()

    def head(self):
        return run("git", "rev-parse", "HEAD", cwd=self.path).stdout.strip()

    def estimate(self, *args, env=None):
        return run(sys.executable, str(SCRIPT), "--repo", str(self.path), "--json", *args,
                   cwd=self.path, check=False, env=env)

    def level(self, *args):
        result = self.estimate(*args)
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)


class EstimateReviewEffort(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        (self.tmp / "repo").mkdir()
        self.repo = Repo(self.tmp / "repo")
        self.base = self.repo.commit("init", **{"README.md": "hi\n", "CLAUDE.md": PINS, "src__a.py": lines(5)})

    def test_prose_only_is_none(self):
        tip = self.repo.commit(**{"README.md": lines(500), "docs__guide.md": lines(50)})
        self.assertEqual(self.repo.level(tip)["level"], "none")

    def test_up_to_ten_lines_is_low_with_mechanical_note(self):
        tip = self.repo.commit(**{"src__b.py": lines(10)})
        result = self.repo.level(tip)
        self.assertEqual((result["level"], result["lines"]["counted"]), ("low", 10))
        self.assertIn("none if mechanical", result["reason"])

    def test_eleven_to_fifty_lines_is_low_without_mechanical_note(self):
        tip = self.repo.commit(**{"src__b.py": lines(50)})
        result = self.repo.level(tip)
        self.assertEqual(result["level"], "low")
        self.assertNotIn("mechanical", result["reason"])

    def test_more_than_fifty_lines_is_medium(self):
        tip = self.repo.commit(**{"src__b.py": lines(51)})
        self.assertEqual(self.repo.level(tip)["level"], "medium")

    def test_added_and_deleted_lines_both_count(self):
        tip = self.repo.commit(**{"src__a.py": lines(26, "y")})
        result = self.repo.level(tip)
        self.assertEqual((result["lines"]["counted"], result["level"]), (31, "low"))

    def test_markdown_lines_are_not_counted(self):
        tip = self.repo.commit(**{"src__b.py": lines(40), "README.md": lines(500)})
        result = self.repo.level(tip)
        self.assertEqual((result["lines"]["total"], result["level"]), (40, "low"))

    def test_generated_vendored_and_binary_files_are_excluded(self):
        self.repo.commit(**{".gitattributes": "gen/** linguist-generated\nvendor/** linguist-vendored=true\n"
                                              "*.lock -diff\n*.dat binary\n"})
        base = self.repo.head()
        tip = self.repo.commit(**{"gen__api.go": lines(300), "vendor__lib.py": lines(300),
                                  "deps.lock": lines(300), "blob.dat": lines(300), "src__b.py": lines(20)})
        result = self.repo.level(f"{base}..{tip}")
        self.assertEqual(result["lines"], {"total": 620, "generated": 600, "counted": 20})
        self.assertEqual(result["generated_paths"], ["blob.dat", "deps.lock", "gen/api.go", "vendor/lib.py"])
        self.assertEqual(result["level"], "low")

    def test_generated_false_is_counted(self):
        self.repo.commit(**{".gitattributes": "gen/** linguist-generated=false\n"})
        base = self.repo.head()
        tip = self.repo.commit(**{"gen__api.go": lines(60)})
        self.assertEqual(self.repo.level(f"{base}..{tip}")["level"], "medium")

    def test_attributes_are_read_at_the_tip_not_the_working_tree(self):
        tip = self.repo.commit(**{".gitattributes": "gen/** linguist-generated\n", "gen__api.go": lines(300)})
        self.repo.write(".gitattributes", "")
        result = self.repo.level(tip)
        self.assertEqual(result["lines"]["counted"], 1)

    def test_falls_back_to_working_tree_attributes_without_check_attr_source(self):
        shim = self.tmp / "bin"
        shim.mkdir()
        real_git = shutil.which("git")
        (shim / "git").write_text(
            "#!/bin/sh\n"
            "case \" $* \" in *\" check-attr \"*\" --source \"*) echo 'error: unknown option `source`' >&2; exit 129;; esac\n"
            f"exec {real_git} \"$@\"\n")
        (shim / "git").chmod((shim / "git").stat().st_mode | stat.S_IEXEC)
        tip = self.repo.commit(**{".gitattributes": "gen/** linguist-generated\n", "gen__api.go": lines(300)})
        env = {**os.environ, "PATH": f"{shim}{os.pathsep}{os.environ['PATH']}"}
        result = self.repo.estimate(tip, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        body = json.loads(result.stdout)
        self.assertEqual(body["lines"]["counted"], 1)
        self.assertIn("working tree", body["notes"][0])

    def test_pinned_path_is_high_regardless_of_size(self):
        tip = self.repo.commit(**{"auth__deep__token.py": lines(1)})
        result = self.repo.level(tip)
        self.assertEqual(result["level"], "high")
        self.assertEqual(result["pins_hit"][0]["paths"], ["auth/deep/token.py"])
        self.assertIsNone(result["panel_hint"])

    def test_pin_uses_git_glob_semantics(self):
        self.repo.commit(**{"CLAUDE.md": "## High-risk paths\n\n- `src/*.py` — top-level only\n"})
        tip = self.repo.commit(**{"src__deep__x.py": lines(60)})
        result = self.repo.level(tip)
        self.assertEqual((result["level"], result["pins_hit"]), ("medium", []))

    def test_pins_stop_at_the_next_section(self):
        self.repo.commit(**{"CLAUDE.md": "## High-risk paths\n\n- `auth/**` — tokens\n\n## Commands\n\n- `src/**` — build\n"})
        tip = self.repo.commit(**{"src__b.py": lines(1)})
        self.assertEqual(self.repo.level(tip)["pins_hit"], [])

    def test_pin_overrides_generated_exclusion(self):
        self.repo.commit(**{".gitattributes": "auth/** linguist-generated\n"})
        base = self.repo.head()
        tip = self.repo.commit(**{"auth__gen.py": lines(3)})
        self.assertEqual(self.repo.level(f"{base}..{tip}")["level"], "high")

    def test_moving_a_file_out_of_a_pinned_path_hits_the_pin(self):
        self.repo.commit(**{"auth__token.py": lines(30)})
        base = self.repo.head()
        (self.repo.path / "lib").mkdir()
        run("git", "mv", "auth/token.py", "lib/token.py", cwd=self.repo.path)
        tip = self.repo.commit("move")
        result = self.repo.level(f"{base}..{tip}")
        self.assertEqual((result["level"], result["lines"]["counted"]), ("high", 0))

    def test_panel_hint_needs_fifty_lines_and_a_pin(self):
        tip = self.repo.commit(**{"auth__token.py": lines(50)})
        result = self.repo.level(tip)
        self.assertEqual(result["panel_hint"], "eligible for panel-review instead of high")

    def merge_side_branch(self, **side_files):
        run("git", "checkout", "-q", "-b", "side", cwd=self.repo.path)
        self.repo.commit(**side_files)
        run("git", "checkout", "-q", "main", cwd=self.repo.path)
        self.repo.commit(**{"src__main.py": lines(100)})
        run("git", "merge", "-q", "--no-edit", "side", cwd=self.repo.path)
        return self.repo.head()

    def test_merge_commit_is_low(self):
        merge = self.merge_side_branch(**{"src__side.py": lines(100)})
        result = self.repo.level(merge)
        self.assertEqual((result["level"], result["merge"]), ("low", True))

    def test_range_containing_a_merge_is_sized_by_its_lines(self):
        self.merge_side_branch(**{"src__side.py": lines(100)})
        result = self.repo.level(f"{self.base}..HEAD")
        self.assertEqual((result["level"], result["merge"]), ("medium", False))

    def test_merge_touching_a_pin_is_high_without_panel_hint(self):
        merge = self.merge_side_branch(**{"auth__token.py": lines(80)})
        result = self.repo.level(merge)
        self.assertEqual((result["level"], result["panel_hint"]), ("high", None))

    def test_fix_commit_touching_a_pin_is_high_without_panel_hint(self):
        tip = self.repo.commit(**{"auth__token.py": lines(80)})
        result = self.repo.level("--fix-commit", tip)
        self.assertEqual((result["level"], result["panel_hint"]), ("high", None))

    def test_pinned_path_with_spaces_is_one_path(self):
        tip = self.repo.commit(**{"auth__my token.py": lines(1)})
        self.assertEqual(self.repo.level(tip)["pins_hit"][0]["paths"], ["auth/my token.py"])

    def test_fix_commit_is_low(self):
        tip = self.repo.commit(**{"src__b.py": lines(80)})
        self.assertEqual(self.repo.level("--fix-commit", tip)["level"], "low")
        self.assertEqual(self.repo.level(tip)["level"], "medium")

    def test_bare_sha_means_its_parent_to_itself(self):
        self.repo.commit(**{"src__b.py": lines(100)})
        tip = self.repo.commit(**{"src__c.py": lines(4)})
        result = self.repo.level(tip)
        self.assertEqual(result["lines"]["counted"], 4)
        self.assertEqual(result["base"], run("git", "rev-parse", f"{tip}^", cwd=self.repo.path).stdout.strip())

    def test_missing_pin_section_means_no_pins_and_says_so(self):
        self.repo.commit(**{"CLAUDE.md": "# Project\n\n**Pinned paths.**\n\n- `auth/**` — not a pin here\n"})
        tip = self.repo.commit(**{"auth__token.py": lines(1)})
        result = self.repo.level(tip)
        self.assertEqual(result["level"], "low")
        self.assertTrue(any("no `## High-risk paths` heading" in n for n in result["notes"]), result["notes"])

    def test_pin_section_present_adds_no_note(self):
        tip = self.repo.commit(**{"src__b.py": lines(1)})
        self.assertEqual(self.repo.level(tip)["notes"], [])

    def test_no_claude_md_adds_no_note(self):
        (self.repo.path / "CLAUDE.md").unlink()
        self.repo.commit()
        tip = self.repo.commit(**{"src__b.py": lines(1)})
        self.assertEqual(self.repo.level(tip)["notes"], [])

    def test_pin_bullet_may_start_with_dash(self):
        self.repo.commit(**{"CLAUDE.md": "## High-risk paths\n\n- `auth/**` — tokens\n"})
        tip = self.repo.commit(**{"auth__token.py": lines(1)})
        self.assertEqual(self.repo.level(tip)["pins_hit"][0]["pin"], "auth/**")

    def test_pin_bullet_may_start_with_asterisk(self):
        self.repo.commit(**{"CLAUDE.md": "## High-risk paths\n\n* `auth/**` — tokens\n"})
        tip = self.repo.commit(**{"auth__token.py": lines(1)})
        self.assertEqual(self.repo.level(tip)["pins_hit"][0]["pin"], "auth/**")

    def test_malformed_pin_bullet_fails_naming_the_line(self):
        self.repo.commit(**{"CLAUDE.md": "# P\n\n## High-risk paths\n\n- `auth/**` — ok\n- auth/** no backticks\n"})
        tip = self.repo.commit(**{"src__b.py": lines(1)})
        result = self.repo.estimate(tip)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CLAUDE.md:6", result.stderr)

    def test_pins_are_read_at_the_tip(self):
        tip = self.repo.commit(**{"auth__token.py": lines(1)})
        self.repo.write("CLAUDE.md", "")
        self.assertEqual(self.repo.level(tip)["level"], "high")

    def test_unknown_target_fails(self):
        result = self.repo.estimate("nope..HEAD")
        self.assertEqual(result.returncode, 2)

    def test_text_output_leads_with_the_level(self):
        tip = self.repo.commit(**{"src__b.py": lines(51)})
        out = run(sys.executable, str(SCRIPT), "--repo", str(self.repo.path), tip, cwd=self.repo.path).stdout
        self.assertEqual(out.splitlines()[:4], ["medium", "reason: more than 50 changed code lines",
                                               "lines: total 51, generated 0, counted 51", "pins hit: none"])


if __name__ == "__main__":
    unittest.main()
