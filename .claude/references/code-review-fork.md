# Using `/code-review` from a worktree

Moved out of `~/.claude/CLAUDE.md`, which points here. The `reviewer` agent is the default and avoids all of this.

The `/code-review` fork resolves
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
