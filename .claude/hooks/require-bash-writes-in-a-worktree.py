#!/usr/bin/env python3
"""PreToolUse(Bash) hook — a shell command that writes into a repository runs
from a worktree of it.

The rule is `require-edits-in-a-worktree.py`'s, applied to the writes that reach
no edit hook: a redirection, a heredoc, `tee`, `sed -i`, `cp`, `rm`. The path
decides, so a command run from anywhere is read against the repository it would
write into.

Scope is the shell's own writers. git's tree-writing commands (`pull`,
`checkout`, `reset`) are how a primary checkout is maintained and sit outside
it, as do a write from inside a program the command runs (`python -c`, a script,
a make recipe), a path the hook cannot expand, and a relative path in a
directory it cannot expand either. ~/.claude/CLAUDE.md is what holds there.
"""

from __future__ import annotations

import os
import re
import shlex
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _worktree_guard as guard  # noqa: E402

HOOK = "require-bash-writes-in-a-worktree.py"
LEAD = "This command would write into a checkout that is not a worktree:"
UNREADABLE = (
    "This command names a writer — `{word}` — but a quote it opens is never closed, so "
    "the path it would write cannot be read. Close the quote, or split the command.\n"
    "Unreadable: {text}"
)

PUNCTUATION = "();<>|&"
REDIRECTS_OUT = frozenset({">", ">>", ">|", ">&", "&>", "&>>"})
REDIRECTS_IN = frozenset({"<", "<&", "<<", "<<-", "<<<", "<>"})
HEREDOC = "<<"
HERESTRING = "<<<"

SHELLS = frozenset({"bash", "dash", "ksh", "sh", "zsh"})
WRAPPERS = frozenset(
    {"command", "doas", "env", "ionice", "nice", "nohup", "stdbuf", "sudo", "time", "timeout", "xargs"}
)
WRAPPER_VALUE_FLAGS = frozenset({"-C", "-u", "--chdir", "--unset"})
DURATION_SUFFIXES = "smhd"
MAX_SHELL_DEPTH = 4

ALL_POSITIONALS = frozenset(
    {
        "chgrp",
        "chmod",
        "chown",
        "mkdir",
        "mkfifo",
        "patch",
        "rm",
        "rmdir",
        "shred",
        "tee",
        "touch",
        "truncate",
        "unlink",
    }
)
LAST_POSITIONAL = frozenset({"cp", "install", "ln", "mv", "rsync"})
IN_PLACE = frozenset({"gsed", "perl", "ruby", "sed"})
DD = "dd"
DD_TARGET = "of="
TARGET_DIRECTORY_FLAGS = frozenset({"-t", "--target-directory"})
WRITER_WORDS = ALL_POSITIONALS | LAST_POSITIONAL | IN_PLACE | {DD}


@dataclass
class Command:
    """One command in a shell line: its words, and the paths it redirects into."""

    argv: list[str] = field(default_factory=list)
    writes: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.argv or self.writes)


def _tokens(text: str) -> list[str] | None:
    """`text` split the way a shell splits a command, with separators and
    redirections kept as tokens of their own — or None when a quote it opens is
    never closed, which a shell answers by reading on."""
    lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return None


def _is_separator(token: str) -> bool:
    """Whether `token` ends the command before it. Adjacent punctuation arrives
    glued together — `;(` rather than `;` and `(` — so any run of it that is not
    a redirection separates."""
    return bool(token) and all(char in PUNCTUATION for char in token)


def _line_commands(tokens: list[str]) -> tuple[list[Command], str]:
    """The commands in `tokens`, and the heredoc delimiter the line opens.

    A redirection's file descriptor arrives as a token of its own, because shlex
    splits `2>` into `2` and `>`; it is dropped with the redirection so it cannot
    sit in the argv and shift a destination positional.
    """
    commands = [Command()]
    heredoc = ""
    redirect = ""
    for token in tokens:
        if redirect:
            if redirect.startswith(HEREDOC) and redirect != HERESTRING:
                heredoc = token
            elif redirect in REDIRECTS_OUT:
                commands[-1].writes.append(token)
            redirect = ""
        elif token in REDIRECTS_OUT or token in REDIRECTS_IN:
            if commands[-1].argv and commands[-1].argv[-1].isdigit():
                commands[-1].argv.pop()
            redirect = token
        elif _is_separator(token):
            commands.append(Command())
        else:
            commands[-1].argv.append(token)
    return [command for command in commands if command], heredoc


def _commands(cmd: str) -> tuple[list[Command], str]:
    """One `Command` per command in `cmd`, and the tail of it that stayed
    unreadable.

    A heredoc body is skipped: its lines are text rather than commands, and a
    trailing backslash in one is text too — joining it to the next line would
    swallow the terminator and read the rest of the body as commands. A line that
    leaves a quote open is joined to the next instead, which is what a shell does
    with it.
    """
    commands: list[Command] = []
    delimiter = ""
    pending = ""
    for line in cmd.splitlines():
        if delimiter:
            delimiter = "" if line.strip() == delimiter else delimiter
            continue
        pending = f"{pending}\n{line}" if pending else line
        if pending.endswith("\\"):
            pending = pending[:-1]
            continue
        tokens = _tokens(pending)
        if tokens is None:
            continue
        pending = ""
        found, delimiter = _line_commands(tokens)
        commands.extend(found)
    return commands, pending


def _strip_env(argv: list[str]) -> list[str]:
    """`argv` without its leading `VAR=value` assignments."""
    while argv and "=" in argv[0] and argv[0].split("=", 1)[0].isidentifier():
        argv = argv[1:]
    return argv


def _moved(base: Path | None, target: str) -> Path | None:
    """`base` after a `cd` to `target`, or None when the hook cannot say where
    that lands.

    A target carrying a variable it cannot expand — `cd "$T"` after
    `T=$(mktemp -d)` — is the case this exists for. Joining it to `base` yields a
    directory named `$T` *inside* the current one, so every relative path after
    it reads as a write into the checkout the command has actually left.
    """
    expanded = os.path.expandvars(os.path.expanduser(target))
    if "$" in expanded:
        return None
    if os.path.isabs(expanded):
        return Path(expanded)
    return None if base is None else base / expanded


def _after_directory_change(
    argv: list[str], base: Path | None, stack: list[Path | None]
) -> tuple[Path | None, list[str]]:
    """`base` after the command's leading directory change, and the command
    without it. `pushd` and `popd` move as `cd` does, through a stack.

    None carries "the hook lost track of where this runs" forward, so a later
    relative path is declined rather than guessed at.
    """
    name = argv[0]
    if name == "cd":
        return (_moved(base, argv[1]) if argv[1:] else Path.home()), argv[2:]
    if name == "pushd":
        stack.append(base)
        return (_moved(base, argv[1]) if argv[1:] else base), argv[2:]
    if name == "popd":
        return (stack.pop() if stack else base), argv[1:]
    return base, argv


def _is_duration(token: str) -> bool:
    """Whether `token` is a bare duration, which is how `timeout` takes its
    own first argument."""
    return token.rstrip(DURATION_SUFFIXES).replace(".", "", 1).isdigit()


def _skip_wrapper_args(args: list[str]) -> list[str]:
    """`args` without the flags and the duration a wrapper takes for itself."""
    while args:
        if args[0] in WRAPPER_VALUE_FLAGS:
            args = args[2:]
        elif args[0].startswith("-") or _is_duration(args[0]):
            args = args[1:]
        else:
            break
    return args


def _command_word(argv: list[str]) -> tuple[str, list[str]]:
    """The command a segment runs and the arguments it was given, with any
    wrapper in front of it dropped — `env`, `sudo` and `timeout 5` keep the real
    command out of `argv[0]`."""
    rest = _strip_env(argv)
    while rest:
        name = Path(rest[0]).name
        if name not in WRAPPERS:
            return name, rest[1:]
        rest = _strip_env(_skip_wrapper_args(rest[1:]))
    return "", []


def _shell_payload(args: list[str]) -> list[str]:
    """The command a shell was handed, which follows the first short cluster
    carrying a `c` — `-c` alone, or `-lc` and `-ec` with company."""
    for i, token in enumerate(args):
        if token.startswith("-") and not token.startswith("--") and "c" in token[1:]:
            return args[i + 1 : i + 2]
    return []


def _inner_commands(argv: list[str]) -> list[str]:
    """The command strings a segment hands to another shell, which have to be
    read as commands rather than as arguments."""
    for i, token in enumerate(argv):
        name = Path(token).name
        if name == "eval":
            return [" ".join(argv[i + 1 :])]
        if name in SHELLS:
            return _shell_payload(argv[i + 1 :])
    return []


def _split_arguments(args: list[str]) -> tuple[list[str], list[str]]:
    """`args` as its flags and its positionals. A flag's value counts as a
    positional, which only ever widens what is checked."""
    flags = [arg for arg in args if arg.startswith("-") and arg != "-"]
    positionals = [arg for arg in args if not arg.startswith("-")]
    return flags, positionals


def _edits_in_place(flags: list[str]) -> bool:
    """Whether a `sed`/`perl`/`ruby` invocation rewrites its input files. A short
    cluster carries the `i` with company — `-pi`, `-i.bak`."""
    return any(flag == "--in-place" or (not flag.startswith("--") and "i" in flag[1:]) for flag in flags)


def _named_targets(name: str, args: list[str], base: Path | None) -> list[str]:
    """The paths a known writer would write, given its arguments."""
    flags, positionals = _split_arguments(args)
    if name == DD:
        return [arg[len(DD_TARGET) :] for arg in args if arg.startswith(DD_TARGET)]
    if name in IN_PLACE:
        if not _edits_in_place(flags):
            return []
        return [arg for arg in positionals if _exists(arg, base)]
    if name in LAST_POSITIONAL:
        if any(flag in TARGET_DIRECTORY_FLAGS for flag in flags):
            return positionals
        return positionals[-1:]
    if name in ALL_POSITIONALS:
        # `patch` reads its target from the diff it is handed, so a command that
        # names none writes somewhere under the directory it runs in.
        if positionals:
            return positionals
        return [str(base)] if name == "patch" and base is not None else []
    return []


def _resolve(token: str, base: Path | None) -> Path | None:
    """`token` as an absolute path, or None when it names no path this hook can
    settle: a file descriptor, a variable it cannot expand, or a relative path
    in a directory it cannot expand either.

    An absolute token stays settled once the directory is unknown, which is what
    keeps `cd "$T" && rm -rf /a/real/checkout` in scope.
    """
    if not token or token == "-" or token.isdigit():
        return None
    expanded = os.path.expandvars(os.path.expanduser(token))
    if "$" in expanded:
        return None
    if os.path.isabs(expanded):
        return Path(expanded).resolve()
    return None if base is None else (base / expanded).resolve()


def _exists(token: str, base: Path | None) -> bool:
    """Whether `token` names a file that is there — the test that tells a
    `sed -i` file operand from the expression in front of it. A token the hook
    cannot place answers False, so the operand is left alone."""
    resolved = _resolve(token, base)
    return resolved is not None and resolved.exists()


def _names_a_writer(text: str) -> str:
    """The writer an unreadable command mentions, or `""`. Read on text no lexer
    could take apart, so it matches words rather than tokens."""
    if ">" in text:
        return ">"
    words = set(re.findall(r"[\w.-]+", text))
    return next((word for word in sorted(WRITER_WORDS) if word in words), "")


def _target_verdict(token: str, base: Path | None, session: tuple[Path, ...]) -> str | None:
    target = _resolve(token, base)
    if target is None:
        return None
    root = guard.checkout_needing_a_worktree(target)
    if root is None or guard.covered_by_project_hook(root, HOOK, guard.project_directory()):
        return None
    return guard.reason(LEAD, target, root, guard.worktree_for(root, *session))


def scan(cmd: str, base: Path | None, session: tuple[Path, ...], depth: int = 0) -> str | None:
    """Why `cmd`, run from `base`, wants a worktree first — or None when it writes
    into no checkout outside one.

    A `base` of None is a directory the hook could not expand, which leaves only
    absolute paths decidable.
    """
    stack: list[Path | None] = []
    commands, unreadable = _commands(cmd)
    for command in commands:
        argv = _strip_env(command.argv)
        if argv:
            base, argv = _after_directory_change(argv, base, stack)
        for inner in _inner_commands(argv) if depth < MAX_SHELL_DEPTH else []:
            reason = scan(inner, base, session, depth + 1)
            if reason:
                return reason
        name, args = _command_word(argv)
        for token in command.writes + _named_targets(name, args, base):
            reason = _target_verdict(token, base, session)
            if reason:
                return reason
    word = _names_a_writer(unreadable)
    return UNREADABLE.format(word=word, text=unreadable) if word else None


def verdict(payload: dict[str, object]) -> str | None:
    session = guard.session_directories(payload)
    tool_input = payload.get("tool_input") or {}
    cmd = str(tool_input.get("command") or "")  # type: ignore[union-attr]
    if not cmd:
        return None
    return scan(cmd, session[0] if session else Path(".").resolve(), session)


if __name__ == "__main__":
    sys.exit(guard.run(verdict))
