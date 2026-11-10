#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Only repositories under this directory are reminded; unset, every repository is.
AUDITED_ROOT = Path(os.path.expanduser(os.environ.get("REVIEW_AUDIT_ROOT", "/")))
NOTES_REF = "refs/notes/review-audit"
STALE_AFTER_SECONDS = 7 * 24 * 3600
REMIND_EVERY_SECONDS = 24 * 3600
STAMP_DIR = Path.home() / ".cache" / "claude-review-audit-reminder"


def git(cwd, *args):
    result = subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def main_checkout(cwd):
    common_dir = git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common_dir).parent if common_dir else None


def reminded_recently(stamp):
    return stamp.exists() and time.time() - stamp.stat().st_mtime < REMIND_EVERY_SECONDS


def main():
    cwd = json.load(sys.stdin).get("cwd", ".")
    repo = main_checkout(cwd)
    if repo is None or AUDITED_ROOT.resolve() not in repo.resolve().parents:
        return

    last_audit = git(repo, "log", "-1", "--format=%ct", NOTES_REF)
    if last_audit and time.time() - int(last_audit) < STALE_AFTER_SECONDS:
        return

    stamp = STAMP_DIR / repo.name
    if reminded_recently(stamp):
        return
    STAMP_DIR.mkdir(parents=True, exist_ok=True)
    stamp.touch()

    when = (
        time.strftime("%Y-%m-%d", time.localtime(int(last_audit)))
        if last_audit
        else "never"
    )
    message = (
        f"No review audit in {repo.name} for over a week (last: {when}). "
        f"Run /review-audit when convenient."
    )
    print(json.dumps({"systemMessage": message}))


main()
