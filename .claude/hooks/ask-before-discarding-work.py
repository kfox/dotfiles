#!/usr/bin/env python3
"""PreToolUse(Bash) hook — ask before a git command discards uncommitted work
in a tree this session does not own.

A permission rule matches a command's spelling, so it can only ask about a verb:
`git restore` prompted for an unstage that touches nothing, while `git reset
--hard` and `git checkout -- .` discard the same work and went through on the
allow list. This hook reads what the command does instead. It asks when a git
command would throw away working-tree changes, the index's staged content
(`reset --hard`), or a stash, and that command runs in the primary checkout, in
another session's worktree, or somewhere the hook cannot place.

In the session's own linked worktree it stays silent. Reverting a mutation in
your own branch is routine. The tree that has to be protected is the one
somebody else may be standing in.

Commands that move no work are out of scope: `restore --staged`, `reset` without
`--hard`/`--merge`, `checkout <branch>`, `stash` and `stash pop`. When the
command text cannot be parsed and names a discarding subcommand, the hook asks.
"""

from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _worktree_guard as guard  # noqa: E402

# The shell parsing is the write hook's; loading it by path keeps one parser
# rather than two that drift. A load failure allows the call, like any other
# failure in a hook (see `_worktree_guard.run`).
try:
    _spec = importlib.util.spec_from_file_location(
        "_bash_parse", os.path.join(os.path.dirname(os.path.abspath(__file__)), "require-bash-writes-in-a-worktree.py")
    )
    assert _spec and _spec.loader
    parse = importlib.util.module_from_spec(_spec)
    sys.modules[_spec.name] = parse  # dataclasses looks its defining module up here
    _spec.loader.exec_module(parse)
except Exception:
    sys.exit(0)

MAX_SHELL_DEPTH = 4
# git's own options that take a value as the next word.
GLOBAL_VALUE_OPTIONS = frozenset({"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"})
DISCARDING_WORDS = frozenset({"restore", "reset", "checkout", "switch", "clean", "stash", "rm", "worktree"})

LEAD = "This git command would discard uncommitted work in a tree this session does not own:"
UNREADABLE = (
    "This command runs `git {word}`, but a quote it opens is never closed, so what it would "
    "discard cannot be read. Close the quote, or split the command.\nUnreadable: {text}"
)


def _short_flags(flags: list[str]) -> set[str]:
    """Every single-letter flag in `flags`, with clusters (`-SW`) split apart."""
    return {letter for flag in flags if flag.startswith("-") and not flag.startswith("--") for letter in flag[1:]}


def _git_invocation(args: list[str], base: Path | None) -> tuple[Path | None, str, list[str]]:
    """Where a git command runs (after its `-C` and `--work-tree`), its
    subcommand, and the subcommand's arguments."""
    i = 0
    while i < len(args) and args[i].startswith("-"):
        word = args[i]
        name, _, attached = word.partition("=")
        value = attached if attached else (args[i + 1] if name in GLOBAL_VALUE_OPTIONS and i + 1 < len(args) else "")
        if name == "-C" and value:
            base = parse._moved(base, value)
        elif name == "--work-tree" and value:
            base = parse._moved(base, value)
        i += 1 if attached or name not in GLOBAL_VALUE_OPTIONS else 2
    if i >= len(args):
        return base, "", []
    return base, args[i], args[i + 1 :]


def _checkout_discards(args: list[str], base: Path | None) -> bool:
    """Whether a `checkout` overwrites working-tree files rather than moving to
    a branch. Paths after `--`, a second operand, `-f` and `-p` all do. A lone
    operand that names an existing path counts too, because git reads it as one
    when no branch of that name exists."""
    if "--" in args:
        return bool(args[args.index("--") + 1 :])
    flags, positionals = parse._split_arguments(args)
    short = _short_flags(flags)
    if {"f", "p"} & short or {"--force", "--patch", "--ours", "--theirs"} & set(flags):
        return True
    if {"b", "B"} & short or "--orphan" in flags:
        return False
    if len(positionals) > 1:
        return True
    return bool(positionals) and parse._exists(positionals[0], base)


def discards(sub: str, args: list[str], base: Path | None) -> bool:
    """Whether `git <sub> <args>` throws away uncommitted work."""
    flags, positionals = parse._split_arguments(args)
    short = _short_flags(flags)
    long = {flag.split("=", 1)[0] for flag in flags if flag.startswith("--")}
    if sub == "restore":
        staged_only = ("S" in short or "--staged" in long) and not ("W" in short or "--worktree" in long)
        return not staged_only
    if sub == "reset":
        return bool({"--hard", "--merge"} & long)
    if sub == "checkout":
        return _checkout_discards(args, base)
    if sub == "switch":
        return "f" in short or bool({"--force", "--discard-changes"} & long)
    if sub == "clean":
        return not ("n" in short or "--dry-run" in long)
    if sub == "stash":
        return bool(positionals) and positionals[0] in {"drop", "clear"}
    if sub == "rm":
        return "f" in short or "--force" in long
    if sub == "worktree":
        return bool(positionals) and positionals[0] == "remove" and ("f" in short or "--force" in long)
    return False


def _tree(path: Path | None) -> Path | None:
    """The checkout or linked worktree `path` sits in, or None."""
    if path is None:
        return None
    marker = guard._git_marker(path.resolve())
    return marker.parent if marker is not None else None


def _owned(tree: Path | None, session: tuple[Path, ...]) -> bool:
    """Whether `tree` is a linked worktree this session works from."""
    if tree is None:
        return False
    marker = tree / ".git"
    if not marker.is_file() or not guard._is_linked_worktree(marker):
        return False
    return any(_tree(directory) == tree for directory in session)


def scan(cmd: str, base: Path | None, session: tuple[Path, ...], depth: int = 0) -> str | None:
    """Why `cmd`, run from `base`, needs the user's say-so, or None."""
    stack: list[Path | None] = []
    commands, unreadable = parse._commands(cmd)
    for command in commands:
        argv = parse._strip_env(command.argv)
        if argv:
            base, argv = parse._after_directory_change(argv, base, stack)
        for inner in parse._inner_commands(argv) if depth < MAX_SHELL_DEPTH else []:
            reason = scan(inner, base, session, depth + 1)
            if reason:
                return reason
        name, args = parse._command_word(argv)
        if name != "git":
            continue
        where, sub, sub_args = _git_invocation(args, base)
        if not discards(sub, sub_args, where):
            continue
        tree = _tree(where)
        if _owned(tree, session):
            continue
        place = str(tree) if tree else "a directory this hook cannot place"
        return (
            f"{LEAD}\n  command: git {sub} {' '.join(sub_args)}\n  tree:    {place}\n"
            "Approve only if that work is meant to go — another session or a person may be standing in this tree."
        )
    if "git" in unreadable:
        words = set(re.findall(r"[\w-]+", unreadable))
        word = next((w for w in sorted(DISCARDING_WORDS) if w in words), "")
        if word:
            return UNREADABLE.format(word=word, text=unreadable)
    return None


def verdict(payload: dict[str, object]) -> str | None:
    session = guard.session_directories(payload)
    tool_input = payload.get("tool_input") or {}
    cmd = str(tool_input.get("command") or "")  # type: ignore[union-attr]
    if not cmd or "git" not in cmd:
        return None
    return scan(cmd, session[0] if session else Path(".").resolve(), session)


if __name__ == "__main__":
    sys.exit(guard.run(verdict))
