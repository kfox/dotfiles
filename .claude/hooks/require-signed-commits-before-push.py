#!/usr/bin/env python3
"""PreToolUse(Bash) hook — deny a `git push` that would publish an unsigned
commit.

`commit.gpgsign` signs what this machine commits, but a commit made with
signing off, by a tool that bypasses it, or by a rebase that rewrote it
unsigned still pushes, and GitHub then shows it Unverified. A signature
cannot be added after the push without rewriting published history, so the
check runs before it.

The commits checked are the ones the push would publish: everything reachable
from each source it pushes and not already on any remote. `%G?` of G or U is
a good signature; anything else (none, bad, expired, unverifiable) denies.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
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

GOOD_SIGNATURES = frozenset({"G", "U"})
# `git push` options that take a value as the next word.
PUSH_VALUE_OPTIONS = frozenset({"-o", "--push-option", "--repo", "--receive-pack", "--exec"})


def push_sources(args: list[str]) -> list[str]:
    """The local revisions `git push <args>` would publish."""
    positionals: list[str] = []
    flags: set[str] = set()
    i = 0
    while i < len(args):
        word = args[i]
        if word.startswith("-"):
            flags.add(word.split("=", 1)[0])
            i += 2 if word in PUSH_VALUE_OPTIONS else 1
            continue
        positionals.append(word)
        i += 1
    if {"-d", "--delete"} & flags:
        return []
    if {"--all", "--mirror", "--branches"} & flags:
        return ["--branches"]
    refspecs = positionals[1:]
    if not refspecs:
        return ["HEAD"]
    sources = [spec.lstrip("+").split(":", 1)[0] for spec in refspecs]
    return [source for source in sources if source]


def unsigned_commits(where: Path | None, sources: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(where or "."), "log", "--format=%h %G? %s", *sources, "--not", "--remotes"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.split(" ", 2)[1] not in GOOD_SIGNATURES]


def scan(cmd: str, base: Path | None, depth: int = 0) -> str | None:
    stack: list[Path | None] = []
    commands, _ = parse._commands(cmd)
    for command in commands:
        argv = parse._strip_env(command.argv)
        if argv:
            base, argv = parse._after_directory_change(argv, base, stack)
        for inner in parse._inner_commands(argv) if depth < discard.MAX_SHELL_DEPTH else []:
            reason = scan(inner, base, depth + 1)
            if reason:
                return reason
        name, args = parse._command_word(argv)
        if name != "git":
            continue
        where, sub, sub_args = discard._git_invocation(args, base)
        if sub != "push":
            continue
        unsigned = unsigned_commits(where, push_sources(sub_args))
        if unsigned:
            listing = "\n  ".join(unsigned)
            return (
                "This push would publish commits without a good signature (%G? shown):\n  "
                f"{listing}\nRe-sign them before pushing, e.g. "
                "`git rebase --exec 'git commit --amend --no-edit -S' <base>`."
            )
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        cmd = str((payload.get("tool_input") or {}).get("command") or "")
        if "push" not in cmd:
            return 0
        session = guard.session_directories(payload)
        reason = scan(cmd, session[0] if session else Path(".").resolve())
    except Exception:
        return 0
    if reason:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
