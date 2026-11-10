#!/usr/bin/env python3
"""PreToolUse(Bash) hook — a git command that changes a checkout runs in this
session's own worktree.

The write hooks see paths; a git command changes a tree, its index, its HEAD or
its branches without naming any. This hook reads what the git command does and
denies a change to a primary checkout, or to a linked worktree of a repository
this session already has a different worktree of.

Left alone everywhere: commands that only read, `fetch`, `pull` (how a primary
checkout is kept current for reading), `worktree` (how a worktree is made),
`push`, `notes`, `tag` and `config`, which change refs or settings but no tree.
A throwaway clone under the temp directory is left alone too.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

HOOKS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HOOKS)

import _worktree_guard as guard  # noqa: E402


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HOOKS, filename))
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses looks its defining module up here
    spec.loader.exec_module(module)
    return module


# One shell parser and one reading of git's global options, shared with the
# other Bash hooks. A load failure allows the call, like any other hook failure.
try:
    parse = _load("_bash_parse", "require-bash-writes-in-a-worktree.py")
    discard = _load("_discard_hook", "ask-before-discarding-work.py")
except Exception:
    sys.exit(0)

LEAD = "This git command would change a checkout that is not a worktree:"
WRONG_LEAD = "This git command would change a worktree this session does not own:"

CHANGING = frozenset(
    {
        "add",
        "am",
        "checkout",
        "cherry-pick",
        "clean",
        "commit",
        "filter-branch",
        "merge",
        "mv",
        "rebase",
        "reset",
        "restore",
        "revert",
        "rm",
        "switch",
        "update-ref",
    }
)
BRANCH_CHANGING_FLAGS = frozenset(
    {"-d", "-D", "-m", "-M", "-c", "-C", "-f", "-u", "--delete", "--move", "--copy",
     "--force", "--set-upstream-to", "--unset-upstream", "--edit-description"}
)
BRANCH_LISTING_FLAGS = frozenset(
    {"-l", "-a", "-r", "-v", "-vv", "--list", "--all", "--remotes", "--contains",
     "--no-contains", "--merged", "--no-merged", "--points-at", "--show-current",
     "--format", "--sort", "--verbose"}
)
STASH_READS = frozenset({"list", "show"})
APPLY_READS = frozenset({"--check", "--stat", "--numstat", "--summary"})


def changes_tree(sub: str, args: list[str]) -> bool:
    """Whether `git <sub> <args>` changes a checkout's tree, index, HEAD or
    branches."""
    flags, positionals = parse._split_arguments(args)
    names = {flag.split("=", 1)[0] for flag in flags}
    if sub in CHANGING:
        return True
    if sub == "branch":
        if names & BRANCH_CHANGING_FLAGS:
            return True
        return bool(positionals) and not names & BRANCH_LISTING_FLAGS
    if sub == "stash":
        return not positionals or positionals[0] not in STASH_READS
    if sub == "apply":
        return not names & APPLY_READS
    if sub == "symbolic-ref":
        return len(positionals) > 1 or "-d" in names or "--delete" in names
    return False


def _verdict_for(tree: Path, session: tuple[Path, ...], command: str) -> str | None:
    wrong = guard.wrong_worktree_reason(f"{WRONG_LEAD}\n  command:             {command}", tree, session)
    if wrong:
        return wrong
    root = guard.checkout_needing_a_worktree(tree)
    if root is None:
        return None
    return guard.reason(f"{LEAD}\n  command:    {command}", tree, root, guard.worktree_for(root, *session))


def scan(cmd: str, base: Path | None, session: tuple[Path, ...], depth: int = 0) -> str | None:
    """Why `cmd`, run from `base`, has to run in this session's worktree, or None."""
    stack: list[Path | None] = []
    commands, _ = parse._commands(cmd)
    for command in commands:
        argv = parse._strip_env(command.argv)
        if argv:
            base, argv = parse._after_directory_change(argv, base, stack)
        for inner in parse._inner_commands(argv) if depth < discard.MAX_SHELL_DEPTH else []:
            reason = scan(inner, base, session, depth + 1)
            if reason:
                return reason
        name, args = parse._command_word(argv)
        if name != "git":
            continue
        where, sub, sub_args = discard._git_invocation(args, base)
        if not changes_tree(sub, sub_args):
            continue
        tree = discard._tree(where)
        if tree is None:
            continue
        reason = _verdict_for(tree, session, f"git {sub} {' '.join(sub_args)}".strip())
        if reason:
            return reason
    return None


def verdict(payload: dict[str, object]) -> str | None:
    session = guard.session_directories(payload)
    tool_input = payload.get("tool_input") or {}
    cmd = str(tool_input.get("command") or "")  # type: ignore[union-attr]
    if "git" not in cmd:
        return None
    return scan(cmd, session[0] if session else Path(".").resolve(), session)


if __name__ == "__main__":
    sys.exit(guard.run(verdict, decision="deny"))
