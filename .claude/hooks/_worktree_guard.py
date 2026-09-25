"""Repository and worktree detection shared by the global worktree hooks.

A change to a repository belongs in a worktree of that repository. Both hooks
ask the same question of a path — would writing here change a checkout that is
not a worktree? — and differ only in where the path comes from, so the answer
lives here rather than in each of them.
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable
from pathlib import Path

GITDIR_PREFIX = "gitdir:"
HOOK_EVENT = "PreToolUse"
WORKTREE_PARTS = (".claude", "worktrees")

GUIDANCE = '~/.claude/CLAUDE.md, "Where a change gets made"'
APPROVE = (
    "Approve this if the change belongs to the primary checkout itself — a merge, a "
    "release, or something the user is doing there by hand."
)
ENTER = (
    "Call EnterWorktree with a `name`, give the worktree an environment of its own "
    "where the toolchain resolves one by path, and make the change there."
)
# EnterWorktree refuses a `name` from a session already in a worktree, so a
# session that has one is told to use it rather than to enter another.
USE_EXISTING = "This session's worktree of that repository is\n  {worktree}\nMake the change there."


def _admin_dir(marker: Path) -> Path | None:
    """The git admin directory a `.git` file points at, or None when it points at
    nothing readable.

    The file reads `gitdir: <checkout>/.git/worktrees/<name>` in a linked worktree
    and `.git/modules/<name>` in a submodule. The value may be relative — git
    writes one under `worktree.useRelativePaths` — and either form may go through
    a symlink, so it is resolved before being read.
    """
    try:
        text = marker.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not text.startswith(GITDIR_PREFIX):
        return None
    recorded = text[len(GITDIR_PREFIX) :].split("\n", 1)[0].strip()
    return (marker.parent / recorded).resolve() if recorded else None


def _is_linked_worktree(marker: Path) -> bool:
    """Whether a `.git` file belongs to a linked worktree rather than to a
    submodule, whose `.git` file carries the same shape."""
    admin = _admin_dir(marker)
    return admin is not None and admin.parent.name == "worktrees"


def _git_marker(start: Path) -> Path | None:
    """The nearest `.git` at or above `start`, or None when `start` is in no
    repository. It is a directory in a clone and a file in a linked worktree."""
    for directory in (start, *start.parents):
        marker = directory / ".git"
        if marker.exists():
            return marker
    return None


def _under_worktrees_dir(target: Path, root: Path) -> bool:
    """Whether `target` sits under `root`'s `.claude/worktrees/`, which is where a
    worktree is written before it has a `.git` of its own to be recognized by."""
    if root not in target.parents:
        return False
    return target.relative_to(root).parts[: len(WORKTREE_PARTS)] == WORKTREE_PARTS


def primary_checkout(start: Path) -> Path | None:
    """The clone `start` belongs to, whether `start` is that clone or one of its
    linked worktrees, or None when `start` is in no repository."""
    marker = _git_marker(start)
    if marker is None:
        return None
    if marker.is_dir():
        return marker.parent
    admin = _admin_dir(marker)
    if admin is None:
        return None
    for parent in admin.parents:
        if parent.name == ".git":
            return parent.parent
    return None


def checkout_needing_a_worktree(target: Path) -> Path | None:
    """The checkout `target` would be written in, or None when writing there
    changes no checkout: `target` is outside any repository, or inside a linked
    worktree, which is where a change belongs."""
    marker = _git_marker(target)
    if marker is None:
        return None
    if marker.is_file():
        return None if _is_linked_worktree(marker) else marker.parent
    root = marker.parent
    return None if _under_worktrees_dir(target, root) else root


def worktree_for(root: Path, *directories: Path) -> Path | None:
    """The linked worktree of `root` among `directories`, or None when none of
    them is one. A session's project directory and its working directory can name
    different trees, so a caller asks about both."""
    for directory in directories:
        marker = _git_marker(directory)
        if marker is None or not marker.is_file() or not _is_linked_worktree(marker):
            continue
        if primary_checkout(marker.parent) == root:
            return marker.parent
    return None


def project_directory() -> Path | None:
    """The project whose settings this session loads, which is what decides
    whether a project's own hooks run at all."""
    named = os.environ.get("CLAUDE_PROJECT_DIR", "")
    return Path(named).resolve() if named else None


def session_directories(payload: dict[str, object]) -> tuple[Path, ...]:
    """The directories this session works from, most specific first."""
    cwd = str(payload.get("cwd") or "")
    project = project_directory()
    named = (Path(cwd).resolve() if cwd else None, project)
    return tuple(directory for directory in named if directory is not None)


def covered_by_project_hook(root: Path, hook: str, project: Path | None) -> bool:
    """Whether `root` carries a hook of this name that this session already runs,
    whose prompt would repeat this one's.

    A project hook is wired by that project's settings, so it runs only for a
    session in that project; for a target in any other repository the global hook
    is the only one asking.
    """
    if project is None or primary_checkout(project) != root:
        return False
    return (root / ".claude" / "hooks" / hook).exists()


def reason(lead: str, target: Path, root: Path, worktree: Path | None) -> str:
    """The prompt shown for a write that wants a worktree first."""
    instruction = USE_EXISTING.format(worktree=worktree) if worktree else ENTER
    return (
        f"{lead}\n"
        f"  repository: {root}\n"
        f"  target:     {target}\n"
        f"A change to a repository is made in a worktree of it ({GUIDANCE}).\n"
        f"{instruction}\n{APPROVE}"
    )


def ask(text: str) -> None:
    """Hand the decision to the user, with `text` as the reason."""
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": HOOK_EVENT,
                    "permissionDecision": "ask",
                    "permissionDecisionReason": text,
                }
            }
        )
    )


def run(decide: Callable[[dict[str, object]], str | None]) -> int:
    """Read a hook payload from stdin and ask when `decide` returns a reason.

    A hook that raises becomes an error on every tool call it matches, so a
    failure in here allows the call instead.
    """
    try:
        payload = json.load(sys.stdin)
        text = decide(payload)
    except Exception:
        return 0
    if text:
        ask(text)
    return 0
