---
name: review-audit
description: Measure how code review is going in one repository, from outside the work. Reads the Claude Code transcripts for a period, reports review cost, findings, fix-chain depth and escapes, and records a public-safe summary as a local git note under refs/notes/review-audit. Use when asked to audit reviews, measure the reviewer, or check whether a review-policy change helped. Never runs per change or as a gate.
---

# Review audit

An audit looks back over a period and ends in one page of numbers and at most
one proposed policy change, which the user decides on. It never runs inside a
change, never adds a record to a commit or PR, and never feeds a reviewer's
prompt. Measuring from inside each change is what sank the two earlier attempts
at this.

Scripts are in `scripts/` beside this file. Every command takes
`--repo <any checkout or worktree>`; the default is the current directory.
Scratch output goes in `--out`: the session's scratch directory, or wherever
the project's CLAUDE.md puts temp files.

## Steps

1. **Pick the period.** `review_audit.py last` prints where the previous audit
   ended. Start the day after; for a first audit, start from the last
   review-policy change.

2. **Scan, then report.**

   ```bash
   review_audit.py scan --since YYYY-MM-DD [--until YYYY-MM-DD] --out DIR
   review_audit.py report --out DIR
   ```

   `scan` finds the transcripts under `~/.claude/projects/` for the main
   checkout and every `.claude/worktrees/*` worktree. Pass
   `--extra-project-dir` for a place the repository used to live. Review agents
   are recognized as the `reviewer` agent (and any `--reviewer-type`), the
   panel lanes, `code-review`/`panel-review` forks, a *wrapper* (an agent
   described as a review that ran a review skill), and a *prompted* review: any
   agent whose prompt opens with "Code review, …" or "Review commit <sha>". A
   review whose prompt first names a sibling checkout, such as another repo's
   worktree, belongs to that repo and is left out. A review done in the main
   session without a subagent is not counted. Pass
   `--extra-kind NAME=REGEX` for other review work the project runs, such as a
   module review. A session that ran this skill is left out.

   `report` writes `metrics.json`, `sample.md` and `note-draft.md`, and lists
   the issues and PRs labeled `escaped-review` that were opened in the period
   (`--no-escapes` skips the GitHub lookup). When the repository has issues
   disabled, it lists PRs alone. When the repository has no such label, it
   leaves escapes unfilled for step 4 instead of reporting none.

3. **Hand-check the sample.** `sample.md` holds bullets from the Fixed
   sections of review reports, plus lines of a free-form report that start
   with `Finding` and say it was fixed. Reviewers also list verification there, so a
   bullet is not always a finding. Sort each one:

   - **defect** — a concrete input gives a wrong result before the fix;
   - **contract** — a claim the code made false, or a branch no test reached,
     with no wrong output;
   - **not a finding** — verification, a hook's own fix, a missing changelog
     entry, a refactor.

   Read the fix commit when the bullet alone doesn't settle it. Only the three
   counts go in the note.

4. **Trace each escape.** An escape is a defect found in merged code. Its
   issue carries the `escaped-review` label, or the PR that fixes it does when
   no issue was filed. For each one, find the commit
   that introduced it and its PR, and record the review that PR got, whether
   the path was pinned, whether the defect was visible in that diff, and
   whether catching it needed hardware.

5. **Fill in the draft** — every `<fill in ...>` — and write at most one
   proposal, or "none". Read the numbers against the previous note:

   - Escapes cluster in one area or one review tier: raise that tier or pin
     the path. This is the signal the audit exists for.
   - No escapes and cost falling: there is room to loosen.
   - Fix chains deeper than 2 reappear: the policy is not being followed; fix
     the skill or the agent prompt, don't add a rule.
   - The sample's real share drops: see which kind of finding is noise and
     tighten that part of the reviewer's prompt.

   Escape counts are small; read them as clusters, not rates.

6. **Record it.** `review_audit.py note --file DIR/note-draft.md` attaches the
   note to the tip of the default branch. It refuses a note that names a
   machine path or still has a placeholder. The note stays in this clone,
   which is where `last` reads it. A plain `git push` never sends
   `refs/notes/*`. Don't push the note or suggest pushing it: most
   repositories are shared, and an audit of one person's sessions is not the
   team's record.

## Notes stay local

Push a note only when the user asks for it by name. Before that push, install
the guard with `review_audit.py install-hook`. It refuses any push of a notes
ref whose new notes name a path outside the repository. It chains an existing
`pre-push` hook as `pre-push.local`, and a repository with `core.hooksPath` set
gets told where to wire it instead.

Every note is written as if it will be pushed, since a pushed note is as public
as the repository. It holds numbers, issue
numbers, commit SHAs and the proposal. A path is relative to the repository
root and never climbs out of it. Never put in a note:

- an absolute or home-relative path, a drive or network path, or `..`;
- a session or agent ID, a hostname, a device name or anything else local;
- finding text from the sample.

The note writer and the pre-push guard share one check, `scripts/notepaths.py`.
It also flags a word that starts with `/`, so write skill names without the
slash.

## Tests

```bash
for t in scripts/tests/test_*.py; do python3 "$t"; done
```
