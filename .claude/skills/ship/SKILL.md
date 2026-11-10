---
name: ship
description: >
  Take a change all the way to a pull request that is ready to merge: branch in
  a worktree, implement, commit, review each change once at an effort set by its
  size and risk, open the PR as a draft, watch CI until green, then mark it
  ready for review. Stops before merging — the merge is always the user's. Use
  when asked to implement a non-trivial change, or to take a change through the
  full branch-review-PR workflow ("ship", "land", "take this to a PR"). A
  project's own ship skill, where one exists, overrides this one.
---

# Ship a change

```
worktree → (implement → commit → review that change)* → final pass (if needed)
         → draft PR → CI green → ready for review → STOP
```

**Never merge.** Do not run `gh pr merge`, do not enable auto-merge, and do not
ask to. Hand over a green PR and stop.

Skip this skill for genuinely trivial work — a typo, a one-line fix the user
dictated, a dependency bump — and say you're skipping it and why.

## 0. Learn the project's rules

Before the first edit, read what the project says about itself: `CLAUDE.md`,
`CONTRIBUTING.md`, and the README's development section. Find:

- **The gate.** The command that lints, type-checks and tests: a `make check`,
  `npm test`, `cargo test`, or a pre-commit config. Also the fuller pre-PR
  gate, if there is one.
- **How the environment is created** (`uv sync`, `npm ci`, …) and whether its
  path can be overridden per checkout.
- **Pinned paths**, if the project names any: high-risk files that are reviewed
  at `high` whatever the diff size. If it names none, treat code at a trust
  boundary (auth, secrets, untrusted input) as pinned.
- **Documentation and changelog obligations.** For example, docs updated in the
  same change, or a changelog fragment format.
- **Commit message conventions.**

Where the project and this skill disagree, the project wins.

## 1. Branch, in a worktree

Call `EnterWorktree` with a `name`; skip this if the session is already in one.
Confirm the branch, and rename it to the project's naming before the first
push, since GitHub closes a PR whose head branch is renamed. Where instructions
name a convention, such as a ticket key, follow it; otherwise use
`<type>/<short-slug>` if the project names branches that way. `<type>` is
`feat`, `fix`, `refactor`, `docs`, `test` or `chore`.

**Give the worktree its own environment** wherever the toolchain resolves one by
path, such as a Python `.venv`, `node_modules` or a build tree. Create it the
way the project does, and pass the override on every command that reads it.
Running a gate from the worktree against the primary checkout's environment can
re-point that environment at the worktree. Both checkouts then pass gates
against code they don't contain.

## 2. Implement

- **Fix every site, not the cited one.** Before committing, grep for the
  pattern, predicate or idiom you changed, and fix the other sites in the same
  commit. Unfixed sibling sites are the finding reviews raise most often.
- **Fix, file or drop by `~/.claude/CLAUDE.md` → "Disposing of a finding"**
  (or the project's CLAUDE.md where it says more), and so does every subagent
  this run starts — point its prompt at that section rather than paraphrasing
  it. A related defect beside the change is fixed here as its own commit; a
  guard ships only with the input that reaches it; a guard for a failure never
  seen is neither committed nor filed.
- **Check a claim before writing it.** Check a docstring, comment or doc
  sentence that names code against that code. Don't write a sentence whose job
  is reassurance or exhaustiveness ("no other caller", "the only site") unless a
  search you ran backs it.
- **Prove a test can fail before claiming it covers anything.** Mutate the line
  it covers, watch a named assertion go red, revert, and re-run green.
- **Update the documentation in the same change** wherever the project asks for
  it.

## 3. Commit, then review the change

Run the gate, then commit related changes together with a message that says
*why*. Write the message carefully once. It is not review surface, and is
reworded only if it misstates what the code does, and never after the push.

**Review each change once**, sized by the table under "Reviewing a change" in
`~/.claude/CLAUDE.md`. A *change* is one logical concern: usually one commit,
sometimes a short `BASE..TIP` run of commits. Count changed code lines with
`git diff --numstat <base> <tip> -- ':!*.md'`; don't estimate.

    Agent(subagent_type="reviewer", description="<short-sha>",
          prompt="Worktree: <absolute worktree path>\nTarget: <sha or BASE..TIP>\nEffort: <level>")

Add any machine-local rule the session's instructions give, such as a
`TMPDIR` prefix, and the project's environment override if the project's own
docs don't state it. A panel (`/panel-review`) is an option only for a change
that meets that skill's thresholds, and it replaces the reviewer rather than
adding to it.

- **A small branch gets one review.** When the whole branch is one change under
  about 300 changed code lines, review it once as `origin/<default>..HEAD`.
  That review is also the final pass, so step 4 is skipped.
- **The reviewer's fix commit gets one `low` review, and that ends the chain.**
- **Don't commit or edit in the worktree while a reviewer runs.** It mutates the
  tree and runs the suite.

When it reports, confirm its fix commit is on your branch
(`git branch --contains <fix-sha>`), re-run the gate, and route what it handed
back:

- **Advisory findings** become their own commit here, reviewed by the table,
  when the call is clearly yours; a design decision that is the user's goes to
  them in the step 7 report rather than into the tracker.
- **"Outside this change" findings** are fixed here when related; otherwise
  filed as issues, one per item and linked back to the PR, only if each names
  the caller, the reaching input and the wrong result. The rest are declined. Never list them in the PR
  description; the step 7 report names the issues.

## 4. Final pass

Run a final pass only when the branch had **two or more** reviewed changes:

    Agent(subagent_type="reviewer", description="<branch-slug> final",
          prompt="Worktree: <absolute worktree path>\nTarget: origin/<default>..HEAD\nEffort: medium\nEvery change on this branch has had its own review. Look for interactions between them, not for defects inside one diff.")

Use `medium`, or `high` only when a pinned path changed after its own review.
Its fix commit gets one `low` review. A defect still open afterwards is a stop:
report it and ask before opening the PR.

## 5. Open the PR

Fold each review's `fixup!` commits into the commit they reviewed
(`GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash origin/<default>`) and name
the old and new SHAs in the step 7 report. Then run the project's pre-PR gate
and open it as a draft:

```bash
gh pr create --draft --title "<title>" --body "<why, and what to look at>"
```

The title follows the project's convention where its instructions name one,
otherwise `<type>: <what changed>`.

The body says what the change does, why, and what a reviewer should look at
closely. It does not list review passes or declined findings; those go to the
user in step 7. Don't put machine-specific details in commits, code or the PR:
local paths, hostnames, IP addresses, device names.

## 6. Watch until green

```bash
gh pr checks --watch
```

After every push, also read code-scanning alerts and PR comments. A CI failure
that is a real defect gets its fix reviewed by step 3's table. An
infrastructure failure, such as a runner that never started, gets a re-run
(`gh run rerun <id> --failed`) and a note in the report.

When every check is green and nothing is left to commit, run `gh pr ready`. If
more work turns up after that, `gh pr ready --undo` until it is done.

## 7. Stop

Report to the user:

- the PR URL, its check status, and whether it is marked ready;
- each review that ran: its target, its effort, what it fixed and what it
  declined, with reasons;
- advisory findings and where each went;
- the issues filed for "Outside this change" findings;
- anything still open.

Then stop. The merge is the user's.
