#!/usr/bin/env python3
"""pre-push guard: refuse to publish git notes that name a machine path.

Git feeds a pre-push hook one line per ref on stdin:
``<local ref> <local sha> <remote ref> <remote sha>``. Pushing a notes ref
publishes every commit in its history, so every note blob the remote lacks is
checked, not only the notes at the tip. The guard fails closed: a note it
cannot read, or a git command that fails, blocks the push.
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notepaths import find_machine_paths  # noqa: E402

NOTES_PREFIX = "refs/notes/"


def _git(*args, stdin=None):
    return subprocess.run(["git", *args], input=stdin, capture_output=True, check=True).stdout


def _is_zero(sha):
    return set(sha) == {"0"}


def _known(sha):
    return subprocess.run(["git", "cat-file", "-e", sha + "^{commit}"], capture_output=True).returncode == 0


def _unpublished_blobs(local_sha, remote_sha):
    spec = [local_sha]
    if not _is_zero(remote_sha) and _known(remote_sha):
        spec += ["--not", remote_sha]
    names = {}
    for line in _git("rev-list", "--objects", *spec).decode().splitlines():
        sha, _, name = line.partition(" ")
        names[sha] = name
    if not names:
        return []
    kinds = _git("cat-file", "--batch-check=%(objectname) %(objecttype)",
                 stdin="\n".join(names).encode() + b"\n").decode().splitlines()
    return [(sha, names[sha]) for sha, kind in (k.split() for k in kinds) if kind == "blob"]


def violations(push_lines):
    found = []
    for line in push_lines:
        fields = line.split()
        if len(fields) != 4:
            continue
        local_ref, local_sha, remote_ref, remote_sha = fields
        if _is_zero(local_sha):
            continue
        if not (local_ref.startswith(NOTES_PREFIX) or remote_ref.startswith(NOTES_PREFIX)):
            continue
        for blob, name in _unpublished_blobs(local_sha, remote_sha):
            try:
                text = _git("cat-file", "blob", blob).decode("utf-8")
            except UnicodeDecodeError:
                found.append((remote_ref, name, "unreadable note", "not UTF-8 text"))
                continue
            found += [(remote_ref, name, rule, token) for rule, token in find_machine_paths(text)]
    return found


def main():
    try:
        found = violations(sys.stdin.read().splitlines())
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"notes guard: could not inspect the push ({exc}); refusing it.", file=sys.stderr)
        return 1
    if not found:
        return 0
    print("notes guard: refusing to push notes that name a machine path.", file=sys.stderr)
    print("A note may name a file only by a path relative to the repository root.", file=sys.stderr)
    for ref, name, rule, token in found:
        print(f"  {ref} note {name.replace('/', '')}: {rule}: {token}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
