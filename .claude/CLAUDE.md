# Coding Guidelines

When writing, refactoring, or reviewing code, follow the
`pairing-with-the-future` skill.

**Comments.** The code is the narrative. Comment only what the code cannot say
through a name, a smaller function, or a named constant: an external
constraint (an API that rejects a value, a limit, a name another file must
match), or why something that looks wrong is right. Never describe what the
code does; the why behind a design belongs in the commit message. A subagent
that writes or fixes code gets this paragraph in its prompt, since it will not
load the skill on its own.

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

Three habits. They cost a minute and they are the difference between a fix and
a plausible fix.

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

## Adding a guard

**A guard ships only with the input that reaches it.** A check, retry,
fallback or validation names three things: the caller at `file:line`, the
value, and the wrong result without the guard. That input comes from an
observed failure, an external contract, or a trust boundary. A value this code
produced, or one its types already rule out, is not an input. The guard's test
feeds that input and fails without it; a guard no test can reach is dead code.
Guards for failures never seen go in the PR body as proposed follow-ups, not in
the diff.

**At a trust boundary the bar is reachability, not likelihood.** The attacker
chooses the input, so cite the path from entry point to sink instead of
arguing odds. Validate once where the value enters, not again at each layer it
passes through. A finding with no path is declined as unreachable.

## Reviewing a change

**One review per change, at an effort its size and risk call for.** A change
is one logical concern: usually one commit, sometimes a short run of commits
reviewed as one `BASE..TIP` range, never a whole multi-concern branch. A branch
that is a single change under about 300 changed code lines gets one review,
and that review is also its final pass.

*Changed code lines* is the added + deleted count from
`git diff --numstat <base> <tip> -- ':!*.md'`. Count them with that command;
don't estimate from the diff.

| Change | Review |
|---|---|
| Prose-only (below) | none |
| Trivial: ≤10 changed code lines, mechanical (rename, typo, dictated line, dependency bump), no pinned path | none |
| ≤50 changed code lines, a merge or conflict resolution, or a reviewer's fix commit | `low` |
| Anything else | `medium` |
| Touches a path the project pins as high-risk | `high` |
| Eligible for a panel by `panel-review`'s "When a panel is an option" | optionally `/panel-review`, *instead of* the reviewer at `high` |

**A reviewer's fix commit gets one `low` review, and that ends the chain.**
What that second pass finds, it fixes, and nothing reviews it again; anything
needing more depth goes to the final pass or to the user.

**A prose-only change is exempt, and a command decides what counts as one, not
the diff's size.** If `git diff <old> <new> -- ':!*.md'` is empty, the change is
prose-only and needs no review. A comment inside a code file is still code. So
is anything in Markdown that the code has to match: a code block, a table of
constants, a documented default. Those keep their review.

**Recording a measured result is prose-only by that test, and needs its
evidence named instead of a review.** Flipping a "verified" cell, or updating a
figure from a run just made, must name the run in the report that reaches the
user: the command, the frame, the exit record. A result nobody can point to is
a claim, and claims get reviewed.

**Folding a prose-only change into a reviewed commit does not void that
commit's review.** The SHA changes, but the empty `':!*.md'` diff between the
old and new SHAs shows the reviewed code is the same, so the review still
stands. Keep the old SHA on a branch until the push, and put the diff command
and its empty result in the report.

**Which reviewer.** The default is the cheap one, and escalation is a claim
about the commit rather than about the code's quality.

- The `reviewer` agent — the default. `Agent(subagent_type="reviewer")` with
  three lines of prompt: the absolute worktree path, the target, the effort. It
  works in that worktree, fixes what it finds as one commit, and reports. A
  project's own `reviewer` agent overrides the user-level one. Do not wrap
  `/code-review` in a general-purpose agent: the wrapper repeats setup and
  gates and costs most of what the review does, and the fork reads the primary
  checkout rather than the worktree.
- `/panel-review <sha>` — four lane reviewers (Auditor, Adversary, Steward,
  Pragmatist), each fixing in its own lane. An optional choice for a change
  that meets the eligibility thresholds in the `panel-review` skill's "When a
  panel is an option", which is the one place they are defined. It replaces the
  reviewer for that change and never stacks on it.

A panel costs roughly a whole session at default models and is not the default
for that reason. Escalating one change in a stack is ordinary; needing to
escalate all of them means the stack is the wrong shape, and splitting it is the
cheaper fix.

Review attention is the scarce resource, and a wide scope spends it before it
reaches the small change. A clean wide pass is evidence of dilution at least as
often as it is evidence of clean code.

A final branch-wide pass is the *second* net, once, before the PR, at
`medium` — and only when the branch had two or more reviewed changes. Never
as the first net.

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

**Confirm the review read the tree you meant.** The `reviewer` agent checks
its target against the worktree's branch before reading, and its fix commit
must show up in `git branch --contains` for that branch. Where `/code-review`
is used anyway, the rest of this section applies. The `/code-review` fork resolves
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
that loop has no fixed point. A finding that cannot be written as actor, action
and wrong result is out of scope — answer "declined, prose" and spend nothing
further on it.

A comment that restates the code is the exception: it is a finding, not prose.
Its actor, action, and wrong result are always the same — every later reader
pays to read it, and it goes false the moment the code moves — and its fix is
a deletion, which carries no new claims, so the loop above cannot start.

Commit messages are the one channel where even a false claim usually stays
unfixed, because rewording one changes the SHA and invalidates every recorded
review of that commit and of everything stacked on it. Report what it should
have said and leave the decision upstream.

## Naming a subagent

**A subagent's label says why it exists, in as few characters as will
identify it.** The Agent tool's `description` leads the agent's row in the
agent panel — not by default, but through `subagentStatusLine` in
`~/.claude/settings.json`, whose script prints the label, the token count and
the live progress summary in that order. The default row shows the agent type
instead, so without that script the label is invisible. Name the issue, PR,
commit, file or question the agent is there for: `Issue #678`, `PR#123`,
`a1b2c3d`, `DMA research`, `#532 CI`. Leave out what the row already shows —
the verb "review", the repository, and any type other than `general-purpose`,
which the script prints ahead of the label, so an `adversary` spawned with
`PR#123` shows both. Three short words at most, and a short SHA (7
characters) rather than a full one. Several agents on one target differ by
what they do with it: `a1b2c3d fix`, `a1b2c3d tests`.

## Opening a pull request

**Every PR opens as a Draft** (`gh pr create --draft`), in every repository,
including when a skill's or a project's own recipe omits the flag. A Draft says
the branch is still moving: more commits, reviews, or CI fixes are expected.

**Mark it Ready for Review (`gh pr ready <number>`) only once every change is
done** — all commits pushed, every review run and its fixes landed, all
verification finished, and CI green. Readiness is the signal that the next step
is the merge. If more work turns up after that, convert it back with
`gh pr ready --undo <number>` until it is done again.
