# Coding Guidelines

When writing, refactoring, or reviewing code, follow the
`pairing-with-the-future` skill.

## Where a change gets made

**Every change gets its own git worktree on its own branch; the primary
checkout is for reading.** Call `EnterWorktree` with a `name` before the first
edit — this paragraph is the standing instruction that tool asks for, so no
per-task go-ahead is needed. The checkout is shared with other sessions and
with a human shell, where a `git pull` or a branch switch moves HEAD out from
under uncommitted work, and two writers in one tree hand each other a diff
neither one wrote. `EnterWorktree` lands under `.claude/worktrees/<name>` and
branches from `origin/<default-branch>`; `worktree.baseRef = "head"` branches
from local HEAD instead, for a change that has to stack on unpushed work.

A single-file edit outside any working tree — this file, `settings.json`, a note
in the vault — needs no worktree. A one-line fix inside a repo does: small is
what makes it tempting to type into whatever branch happens to be checked out.

**Where the toolchain resolves an environment by path, the worktree gets its
own.** A Python `.venv`, `node_modules`, a build tree: create it the way the
project creates one (`uv sync`, `npm ci`) and pass the override on every command
that reads it. Running a gate from the worktree against the primary checkout's
environment re-points that environment's editable install at the worktree, so
the next gate run in the primary checkout imports code that checkout does not
contain — and passes. Both halves of that failure are green.

Two hooks ask before a write lands outside a worktree:
`~/.claude/hooks/require-edits-in-a-worktree.py` on the file-editing tools, and
`require-bash-writes-in-a-worktree.py` on the shell's own writers — a
redirection, a heredoc, `tee`, `sed -i`, `cp`, `rm`. A write from inside a
program they run (`python -c`, a script, a make recipe), a path they cannot
expand, and git's own tree commands are outside their scope, so there this rule
is the only thing holding.

## Fixing a reported defect

Three habits, each earned by watching a fix fail review repeatedly. They cost a
minute and they are the difference between a fix and a plausible fix.

- **Fix every site, not the cited one.** A report names where the reporter
  happened to look. Before committing, grep for the pattern, predicate, or shape
  just changed; if a second call site exists, fix it in the same change or say
  why it does not need it. Prefer one shared implementation to two corrected
  copies — two copies is how they drifted.
- **Close the class, not the instance.** Adding one more condition to a test
  usually narrows a bug rather than removing it. Re-run the original
  reproduction with a single field varied; if a near-miss still reproduces, the
  fix is a speed bump. When adding a branch to a classifier, name the default
  explicitly and make sure input matching no branch fails in the safe direction.
  Where one failure mode is silent and the other noisy, choose noisy.
- **Do not claim verification that was not run.** "Tests cover this" means the
  behavior was deliberately broken and a test failed — otherwise say "tests
  exist". Prove claims by execution rather than argument: measured timings, a
  re-run exploit, a mutation. And when a test goes red after a fix, read what it
  asserts before changing it — it may be asserting the bug.

## Reviewing a change

**One review per changeset, scoped to that changeset.** Every commit gets its
own review before it is pushed — that SHA alone, never the branch. There is no
trivial-diff exemption: at low effort a two-line commit costs seconds, and "this
one is obviously fine" is exactly the judgment that fails.

**Which reviewer.** The default is the cheap one, and escalation is a claim
about the commit rather than about the code's quality.

- `/code-review <sha>` — the default, for every commit. One reviewer, one pass.
- `/panel-review <sha>` — four lane reviewers in parallel (Auditor, Adversary,
  Steward, Pragmatist), each fixing in its own lane. Reach for it when the
  commit is large, or when being wrong is expensive: a trust boundary, authn or
  authz, money, data deletion or migration, a public API or wire format,
  concurrency, a bounded resource under load. Also when a single pass came back
  clean on a diff big enough that a clean pass is itself the suspicious result.

A panel costs roughly four passes and is not the default for that reason.
Escalating one commit in a stack is ordinary; needing to escalate all of them
means the stack is the wrong shape, and splitting it is the cheaper fix.

Review attention is the scarce resource, and a wide scope spends it before it
reaches the small commit. A branch-scoped pass over 7.1k lines verified five
separate arithmetic claims and walked past a 3-file commit that doubled a
latency budget; the same reviewer pointed at that commit alone found it
immediately. A clean wide pass is evidence of dilution at least as often as it
is evidence of clean code.

A batch- or branch-wide review is still worth running — as the *second* net,
once, before the PR. Never as the first one.

**Who applies the fix.** A reviewer that finds an in-tree defect fixes it and
hands it back as its own commit, never an amend. Amending the commit under
review changes its SHA, so the review it already passed points at nothing.
This holds for a review subagent, and its prompt has to say so out loud:
`/code-review` without `--fix` is a report-only run, so a subagent told merely
to review leaves the tree untouched and the findings arrive here as prose. The
`/panel-review` lane agents fix by default, so the inverse applies — say
"report only" when that is what you want, or they will commit.

The reviewer already has the worktree, the warm gates and the measurement in
hand; routing "exact replacement text" back through the orchestrator adds a
transcription step that can only lose fidelity. Worse, what the orchestrator
writes from a description is new code, and new code earns a review, which finds
new defects — the hand-back is the loop that spends hours on a minor change.

Two classes stay with the orchestrator. Anything that rewrites a commit message,
because that changes the SHA and invalidates every in-flight review of that
commit and of everything stacked on it. And anything editorial — whether to
repair a sentence or delete its paragraph needs the whole-branch view that a
single-commit reviewer cannot have by construction. Five weak claims across four
commits is a fact about claim density; no one reviewing one commit can see it.

**Confirm the review read the tree you meant.** The `/code-review` fork resolves
its working directory against the session's primary checkout rather than the
caller's, so a review invoked from a worktree can read a different branch end to
end and report it under this one's name. Nothing in the report says so: the
findings come back as ordinary findings about real code. Measured with several
worktrees live at once — one pass reviewed a sibling branch from start to finish
and handed it back as the requester's.

Give it an explicit SHA rather than a range. `origin/main..HEAD` resolves to
*empty* in a clean primary checkout, and the fork then stops to ask which of the
worktrees it should read — a question nobody can answer, because every candidate
belongs to a different agent, and naming one reviews a tree whose owner did not
ask while leaving the real requester still waiting.

Then check the pass before spending anything on it. `git branch -a --contains
<fix-sha>` must name only the reviewed branch: a fix commit can land solely in
the tree the reviewer wrote to, which is what makes it proof. The paths in the
report are not proof — a fork that read the right tree still renders the odd
finding's path in primary-checkout form, so a mismatch there is a reason to look
rather than a verdict. A report with no findings leaves no fix commit to check,
and there the file list it claims goes against `git show --stat <sha>` instead.

The fork is also always named `code-review`, so two callers at once collide on
it and a message addressed to that name reaches whichever registered last —
the earlier one becomes unaddressable. Correct the *reviewer* rather than its
fork: the reviewer has a stable agent id, and a mid-run message to that id
carrying the absolute worktree path has been seen to land and move a reviewer
back onto the right base, with several forks alive and the name already
collided.

Write the review down where the next reader will find it: what you looked at,
what you found, and what you did about each finding. A review that leaves
nothing behind did not happen. Put it in the report that reaches the user, not
into a commit message — prose that a process depends on is prose that has to be
argued about.

**Review claims, not writing.** Documentation is review surface. A docstring, a
README, an architecture note, a schema, a config default and a test name all
make checkable claims about the system, and a claim that has gone false gets
believed by whoever reads it next. Keeping those in step with the code is part
of the change, not a courtesy after it, and drift is an ordinary finding that
gets fixed like any other.

What is not review surface is prose *as writing*: style, tone, precision,
thinness, completeness, whether a sentence could be clearer or a paragraph
better arranged. A finding about one of those does not get reported.

The line between them is whether you can name an actor, an action, and a wrong
result. "The docstring says the timeout is 30s and the code passes 300" names
all three — the next caller sizes a retry budget off that sentence and gets it
wrong. "A reader could be misled" names none of them; it is a feeling about a
sentence, and there is always another sentence.

Two shapes sit close to the line and are worth calling by name. A claim that is
merely *absent* — an undocumented decision, a thin commit message — is not a
false claim, so it is not a finding; write the missing prose if it is cheap and
say nothing if it is not. And a claim that is false only about *intent* rather
than behavior is out too: the code is the authority on what it does, and a
comment that describes the same behavior less well than the code does is
writing, not drift.

This is a scope rule, not a severity rule. Downgrading a writing quibble to
"low" does not make it cheap — someone still reads it, decides, and writes down
why, which is a full round spent on a sentence. And the fix for a writing
finding is more writing, which carries new claims, which yields new findings:
that loop has no fixed point, and it is why the review gates here were retired
rather than tuned. A finding that cannot be written as actor, action and wrong
result is out of scope — answer "declined, prose" and spend nothing further
on it.

Commit messages are the one channel where even a false claim usually stays
unfixed, because rewording one changes the SHA and invalidates every recorded
review of that commit and of everything stacked on it. Report what it should
have said and leave the decision upstream.
