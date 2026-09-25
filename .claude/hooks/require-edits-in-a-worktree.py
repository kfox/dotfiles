#!/usr/bin/env python3
"""PreToolUse(Edit|Write|NotebookEdit) hook — a change to a repository is made
in a worktree of it.

The target path decides, not the session's directory: an edit reaching into some
other repository's primary checkout changes that checkout just as much as one
reaching into this session's.

The decision is `ask` rather than `deny`, because a primary checkout has changes
that belong to it — a merge, a release, an edit the user is making by hand — so
the point is to make writing there deliberate rather than impossible.

Only the file-editing tools reach here. A write driven through the shell is
`require-bash-writes-in-a-worktree.py`'s decision.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _worktree_guard as guard  # noqa: E402

HOOK = "require-edits-in-a-worktree.py"
LEAD = "This edit would land in a checkout that is not a worktree:"
PATH_KEYS = ("file_path", "notebook_path")


def _target(tool_input: dict[str, object], session: tuple[Path, ...]) -> Path | None:
    """The path this call would write, or None when it names none."""
    named = next((tool_input[key] for key in PATH_KEYS if tool_input.get(key)), "")
    if not named:
        return None
    working = session[0] if session else Path(".").resolve()
    return (working / os.path.expanduser(str(named))).resolve()


def verdict(payload: dict[str, object]) -> str | None:
    """Why this edit wants a worktree first, or None when it does not need one."""
    session = guard.session_directories(payload)
    target = _target(payload.get("tool_input") or {}, session)  # type: ignore[arg-type]
    if target is None:
        return None
    root = guard.checkout_needing_a_worktree(target)
    if root is None or guard.covered_by_project_hook(root, HOOK, guard.project_directory()):
        return None
    return guard.reason(LEAD, target, root, guard.worktree_for(root, *session))


if __name__ == "__main__":
    sys.exit(guard.run(verdict))
