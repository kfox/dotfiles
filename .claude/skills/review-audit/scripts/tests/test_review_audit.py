import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import review_audit  # noqa: E402

REPORT = """## Review: abc1234 (medium) in the worktree
Fix commit: def5678 | `git branch -a --contains` lists only this branch.
### Fixed
- c64cast/a.py:10 — off by one — verified by mutation
- c64cast/b.py:3 — unfixed sibling
  - **Verified by:** a test that fails without it
### Advisory
- none
### Declined
- a doc nit — prose
### Checked clean
- the gate
"""


class ParseReport(unittest.TestCase):
    def test_reviewer_report_sections_and_fix(self):
        sections, fixed, fix = review_audit.parse_report(REPORT, "abc1234")
        self.assertEqual((sections["fixed"], sections["advisory"], sections["declined"]), (2, 0, 1))
        self.assertEqual(fix, "def5678")
        self.assertEqual(len(fixed), 2)

    def test_json_findings_are_counted_as_reported(self):
        sections, _, _ = review_audit.parse_report('```json\n[{"file": "a.py"}, {"file": "b.py"}]\n```', None)
        self.assertEqual(sections["reported"], 2)

    def test_lane_report_findings_and_fix(self):
        text = ("## Auditor report: e7c614a and e86b04e\n"
                "It is fixed in **a682a9e** on `review/x`.\n"
                "**Finding A1 (warning; fixed in a682a9e).** Location: models.go\n"
                "**Finding A2, warning, not fixed: one call has no limit.**\n"
                "**Findings:** none.\n")
        sections, fixed, fix = review_audit.parse_report(text, "e7c614a", {"e7c614a", "e86b04e"})
        self.assertEqual((sections["fixed"], sections["reported"]), (1, 1))
        self.assertTrue(fixed[0].startswith("**Finding A1"))
        self.assertEqual(fix, "a682a9e")

    def test_prose_findings_beside_a_heading(self):
        text = "**Finding B1, warning, fixed in 5525e7b.** At events.go\n### Advisory, out of scope\n- labels\n"
        sections, fixed, _ = review_audit.parse_report(text, None)
        self.assertEqual((sections["fixed"], sections["advisory"]), (1, 1))

    def test_fix_sha_after_a_few_words(self):
        _, _, fix = review_audit.parse_report("One fix commit came out of it: **5525e7b**.", None)
        self.assertEqual(fix, "5525e7b")

    def test_no_fix_commit_names_no_fix(self):
        text = "I made no fix commits, the branch is still dc37215 then 437c3a9."
        self.assertIsNone(review_audit.parse_report(text, None)[2])

    def test_a_reviewed_commit_is_not_the_fix(self):
        text = "Two reviews. Fixed nothing in 437c3a9."
        self.assertIsNone(review_audit.parse_report(text, "dc37215", {"dc37215", "437c3a9"})[2])

    def test_prose_clean_verdict(self):
        for text in ("I reviewed 8c4615a on its own and found no defects.",
                     "Review of 72a50e5: **Findings:** none.",
                     "Neither commit has a correctness defect."):
            sections, _, _ = review_audit.parse_report(text, None)
            self.assertEqual(sections["clean verdict"], 1, text)


class Classify(unittest.TestCase):
    def kind(self, meta=None, forked=None, prompt="", extra=(), kinds=()):
        return review_audit.classify(meta or {}, forked or {}, prompt, set(extra),
                                     [review_audit.extra_kind(k) for k in kinds])

    def test_kinds(self):
        self.assertEqual(self.kind({"agentType": "reviewer"}, prompt="Worktree: w\nTarget: abc1234\nEffort: low."),
                         "reviewer:low")
        self.assertEqual(self.kind({"agentType": "reviewer"}), "reviewer:unstated")
        self.assertEqual(self.kind({"agentType": "auditor"}), "lane:auditor")
        self.assertEqual(self.kind(forked={"skillName": "code-review", "effort": "high"}), "code-review:high")
        self.assertEqual(self.kind({"agentType": "checker"}, prompt="Effort: high", extra=["checker"]),
                         "checker:high")
        self.assertEqual(self.kind({"description": "SID-6 finder"}, prompt="c64cast module review, unit SID-6",
                                   kinds=["module-review=module review"]), "module-review")
        self.assertIsNone(self.kind({"description": "review abc1234"}))

    def test_a_general_agent_asked_for_a_review(self):
        gp = {"agentType": "general-purpose"}
        self.assertEqual(self.kind(gp, prompt="Code review, medium effort, of exactly ONE commit: 72a50e5"),
                         "prompted:medium")
        self.assertEqual(self.kind(gp, prompt="Two separate code reviews, low effort. First"), "prompted:low")
        self.assertEqual(self.kind(gp, prompt="Review commit 8c4615ad4157 in the repo, and fix what you find."),
                         "prompted:unstated")
        self.assertIsNone(self.kind(gp, prompt="Implement SECENG-1 and get a code review of it"))
        self.assertIsNone(self.kind(gp, prompt="Read-only audit of the service; review every file"))


class OtherCheckout(unittest.TestCase):
    def test_a_prompt_naming_only_a_sibling_checkout(self):
        here = Path("/src/github.com/app")
        self.assertTrue(review_audit.names_other_checkout(
            "Code review of 72a50e5 in the worktree /src/github.com/infra/.claude/worktrees/x", here))
        self.assertFalse(review_audit.names_other_checkout(
            "Code review in /src/github.com/app/.claude/worktrees/x, compare /src/github.com/infra", here))
        self.assertFalse(review_audit.names_other_checkout("Review commit abc1234 in this repo", here))
        self.assertTrue(review_audit.names_other_checkout("Code review in /src/github.com/app-two/x", here))
        self.assertTrue(review_audit.names_other_checkout(
            "Code review in /src/github.com/infra/.claude/worktrees/x; the consumer is /src/github.com/app", here))

    def test_an_agent_that_runs_a_review_skill_is_a_wrapper(self):
        def agent(aid, description, kind=None, calls=(), parent=None):
            return {"id": aid, "kind": kind, "skill_calls": list(calls), "prompt": "",
                    "meta": {"description": description, "parentAgentId": parent}}

        agents = [
            agent("w", "review abc1234"),
            agent("f", "", kind="code-review:medium", parent="w"),
            agent("i", "review def5678", calls=[{"skill": "code-review"}]),
            agent("h", "review the hardware run"),
            agent("m", "implement #12 and review it", calls=[{"skill": "code-review"}]),
        ]
        review_audit.mark_wrappers(agents)
        self.assertEqual([a["kind"] for a in agents],
                         ["wrapper", "code-review:medium", "wrapper", None, None])


class Escapes(unittest.TestCase):
    def test_a_repo_with_issues_disabled_still_lists_prs(self):
        def fake_run(cmd, **kwargs):
            if cmd[1] == "issue":
                raise subprocess.CalledProcessError(
                    1, cmd, stderr="the 'o/r' repository has disabled issues\n")
            out = '[{"name": "escaped-review"}]' if cmd[1] == "label" else '[{"number": 7}]'
            return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr="")
        real, review_audit.subprocess.run = review_audit.subprocess.run, fake_run
        try:
            found = review_audit.escapes(Path("."), {"since": "2026-10-01", "until": "2026-10-02"})
        finally:
            review_audit.subprocess.run = real
        self.assertEqual(found, [7])

    def test_a_repo_without_the_label_collects_nothing(self):
        def fake_run(cmd, **kwargs):
            out = "[]" if cmd[1] == "label" else '[{"number": 7}]'
            return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr="")
        real, review_audit.subprocess.run = review_audit.subprocess.run, fake_run
        try:
            found = review_audit.escapes(Path("."), {"since": "2026-10-01", "until": "2026-10-02"})
        finally:
            review_audit.subprocess.run = real
        self.assertIsNone(found)

    def test_other_gh_failures_still_stop_the_report(self):
        def fake_run(cmd, **kwargs):
            raise subprocess.CalledProcessError(1, cmd, stderr="HTTP 401: Bad credentials\n")
        real, review_audit.subprocess.run = review_audit.subprocess.run, fake_run
        try:
            with self.assertRaises(subprocess.CalledProcessError):
                review_audit.escapes(Path("."), {"since": "2026-10-01", "until": "2026-10-02"})
        finally:
            review_audit.subprocess.run = real


class ChainDepths(unittest.TestCase):
    def test_review_of_a_fix_commit_extends_the_chain(self):
        units = [
            {"session": "s", "t0": 1, "target": "aaaaaaa", "fix": "bbbbbbb"},
            {"session": "s", "t0": 2, "target": "bbbbbbb", "fix": None},
            {"session": "s", "t0": 3, "target": "ccccccc..ddddddd", "fix": None},
        ]
        self.assertEqual(review_audit.chain_depths(units), ({1: 1, 2: 1}, 1))


def line(**entry):
    return json.dumps(entry) + "\n"


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "repo"
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True, timeout=60)
        self.project = self.tmp / "project"
        sub = self.project / "s1" / "subagents"
        sub.mkdir(parents=True)
        (self.project / "s1.jsonl").write_text(
            line(type="user", timestamp="2026-10-22T10:00:00Z", message={"content": "do work"})
            + line(type="assistant", timestamp="2026-10-22T10:01:00Z",
                   message={"id": "m1", "usage": {"input_tokens": 100, "output_tokens": 0}, "content": []}))
        (sub / "agent-r1.jsonl").write_text(
            line(type="user", timestamp="2026-10-22T10:02:00Z",
                 message={"content": "Worktree: w\nTarget: abc1234\nEffort: medium"})
            + line(type="assistant", timestamp="2026-10-22T10:03:00Z",
                   message={"id": "m2", "usage": {"input_tokens": 300, "output_tokens": 0},
                            "content": [{"type": "tool_use", "name": "SubagentHandback",
                                         "input": {"message": REPORT}}]}))
        (sub / "agent-r1.meta.json").write_text(json.dumps({"agentType": "reviewer", "description": "abc1234"}))
        (self.project / "old.jsonl").write_text(
            line(type="user", timestamp="2026-09-01T10:00:00Z", message={"content": "old"}))

    def test_scan_and_report(self):
        out = self.tmp / "out"
        common = ["--repo", str(self.repo)]
        printed = io.StringIO()
        with redirect_stdout(printed):
            review_audit.main(common + ["scan", "--since", "2026-10-21", "--until", "2026-10-27",
                                        "--out", str(out), "--extra-project-dir", str(self.project)])
            review_audit.main(common + ["report", "--out", str(out), "--no-escapes"])
        self.assertIn("1 sessions", printed.getvalue())
        metrics = json.loads((out / "metrics.json").read_text())
        self.assertEqual(metrics["sessions"], 1)
        self.assertEqual(metrics["tokens"], {"total": 400, "review": 300, "review_share": 0.75})
        self.assertEqual(metrics["reviews"], {"reviewer:medium": {"count": 1, "tokens": 300}})
        self.assertEqual(metrics["findings"]["fixed"], 2)
        self.assertEqual((metrics["reviews_clean"], metrics["reviews_unparsed"]), (0, 0))
        draft = (out / "note-draft.md").read_text()
        self.assertIn("since: 2026-10-21", draft)
        self.assertNotIn(str(self.tmp), draft)


if __name__ == "__main__":
    unittest.main()
