#!/usr/bin/env python3
"""Compute the review level for one change, per "Reviewing a change" in ~/.claude/CLAUDE.md."""

import argparse
import json
import re
import subprocess
import sys

NOT_MARKDOWN = ":!*.md"
PIN_SECTION = "## High-risk paths"
PIN_BULLET = re.compile(r"^[-*] `([^`]+)`\s+[—–-]+\s+(\S.*)$")
LIST_MARKER = re.compile(r"^[-*+]\s")
TRIVIAL_LINES = 10
LOW_LINES = 50
PANEL_LINES = 50
GENERATED_ATTRS = ("linguist-generated", "linguist-vendored")
TRUTHY_ATTR_VALUES = ("set", "true")


class EstimateError(Exception):
    pass


def git(repo, *args, check=True):
    result = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise EstimateError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result


def resolve_commit(repo, rev):
    return git(repo, "rev-parse", "--verify", "--quiet", rev + "^{commit}").stdout.strip()


def resolve_range(repo, target):
    base, sep, tip = target.partition("..")
    if not sep:
        base, tip = target + "^", target
    if not base or not tip or tip.startswith("."):
        raise EstimateError(f"target {target!r} is not BASE..TIP or a SHA")
    return resolve_commit(repo, base), resolve_commit(repo, tip)


def numstat(repo, base, tip):
    out = git(repo, "diff", "--numstat", "-z", "-M", base, tip, "--", NOT_MARKDOWN).stdout
    fields = out.split("\0")
    counts = {}
    i = 0
    while i < len(fields) and fields[i]:
        added, deleted, path = fields[i].split("\t", 2)
        if not path:
            path = fields[i + 2]
            i += 3
        else:
            i += 1
        counts[path] = sum(int(n) for n in (added, deleted) if n != "-")
    return counts


def check_attr(repo, tip, paths):
    stdin = "\0".join(paths) + "\0"
    attrs = [*GENERATED_ATTRS, "diff"]
    args = ["check-attr", "--stdin", "-z", "--source", tip, *attrs]
    note = None
    result = subprocess.run(["git", "-C", repo, *args], input=stdin, capture_output=True, text=True)
    if result.returncode != 0 and "source" in result.stderr:
        note = "this git has no check-attr --source; attributes were read from the working tree, not the tip"
        args.remove("--source")
        args.remove(tip)
        result = subprocess.run(["git", "-C", repo, *args], input=stdin, capture_output=True, text=True)
    if result.returncode != 0:
        raise EstimateError(f"git check-attr: {result.stderr.strip()}")
    values = {}
    fields = result.stdout.split("\0")
    for path, attr, value in zip(fields[0::3], fields[1::3], fields[2::3]):
        values.setdefault(path, {})[attr] = value
    return values, note


def is_generated(attr_values):
    if any(attr_values.get(a) in TRUTHY_ATTR_VALUES for a in GENERATED_ATTRS):
        return True
    return attr_values.get("diff") == "unset"


def parse_pins(claude_md):
    lines = claude_md.splitlines()
    try:
        start = lines.index(PIN_SECTION)
    except ValueError:
        return None
    pins = []
    for number, line in enumerate(lines[start + 1:], start=start + 2):
        if re.match(r"^#{1,2} ", line):
            break
        if not LIST_MARKER.match(line):
            continue
        match = PIN_BULLET.match(line)
        if not match:
            raise EstimateError(f"CLAUDE.md:{number}: pin bullet is not \"- `<pathspec glob>` — reason\": {line}")
        pins.append((match.group(1), match.group(2)))
    return pins


def read_pins(repo, tip):
    """The tip's pins, and a note when its CLAUDE.md has no pin section to read."""
    shown = git(repo, "show", f"{tip}:CLAUDE.md", check=False)
    if shown.returncode != 0:
        return [], None
    pins = parse_pins(shown.stdout)
    if pins is None:
        return [], f"CLAUDE.md has no `{PIN_SECTION}` heading, so no path is pinned; pins written any other way are not read"
    return pins, None


def pin_hits(repo, base, tip, pins):
    hits = []
    for pin, reason in pins:
        out = git(repo, "diff", "--name-only", "-z", base, tip, "--", f":(glob){pin}", NOT_MARKDOWN).stdout
        paths = [p for p in out.split("\0") if p]
        if paths:
            hits.append({"pin": pin, "reason": reason, "paths": paths})
    return hits


def is_merge_resolution(repo, base, tip):
    parents = git(repo, "rev-list", "--parents", "-n", "1", tip).stdout.split()[1:]
    return len(parents) > 1 and parents[0] == base


def estimate(repo, target, fix_commit=False):
    base, tip = resolve_range(repo, target)
    result = {
        "level": None, "reason": None, "base": base, "tip": tip,
        "lines": {"total": 0, "generated": 0, "counted": 0},
        "generated_paths": [], "pins_hit": [], "merge": is_merge_resolution(repo, base, tip),
        "fix_commit": fix_commit, "panel_hint": None, "notes": [],
    }
    if git(repo, "diff", "--quiet", base, tip, "--", NOT_MARKDOWN, check=False).returncode == 0:
        result["level"] = "none"
        result["reason"] = "prose-only: no change outside Markdown"
        return result

    counts = numstat(repo, base, tip)
    attrs, note = check_attr(repo, tip, list(counts))
    if note:
        result["notes"].append(note)
    generated = sorted(p for p in counts if is_generated(attrs.get(p, {})))
    total = sum(counts.values())
    excluded = sum(counts[p] for p in generated)
    counted = total - excluded
    result["lines"] = {"total": total, "generated": excluded, "counted": counted}
    result["generated_paths"] = generated
    pins, pin_note = read_pins(repo, tip)
    if pin_note:
        result["notes"].append(pin_note)
    result["pins_hit"] = pin_hits(repo, base, tip, pins)

    if result["pins_hit"]:
        result["level"] = "high"
        result["reason"] = "touches a pinned high-risk path"
        if counted >= PANEL_LINES and not (fix_commit or result["merge"]):
            result["panel_hint"] = "eligible for panel-review instead of high"
    elif counted <= TRIVIAL_LINES:
        result["level"] = "low"
        result["reason"] = f"≤{TRIVIAL_LINES} lines: none if mechanical (rename, typo, dictated line, dependency bump)"
    elif counted <= LOW_LINES:
        result["level"] = "low"
        result["reason"] = f"≤{LOW_LINES} changed code lines"
    elif result["merge"]:
        result["level"] = "low"
        result["reason"] = "a merge resolution"
    elif fix_commit:
        result["level"] = "low"
        result["reason"] = "a reviewer's fix commit"
    else:
        result["level"] = "medium"
        result["reason"] = f"more than {LOW_LINES} changed code lines"
    return result


def render(result):
    lines = result["lines"]
    pins = "; ".join(f"`{h['pin']}` ({', '.join(h['paths'])})" for h in result["pins_hit"]) or "none"
    out = [
        result["level"],
        f"reason: {result['reason']}",
        f"lines: total {lines['total']}, generated {lines['generated']}, counted {lines['counted']}",
        f"pins hit: {pins}",
    ]
    if result["generated_paths"]:
        out.append(f"generated: {', '.join(result['generated_paths'])}")
    if result["panel_hint"]:
        out.append(f"panel: {result['panel_hint']}")
    out += [f"note: {n}" for n in result["notes"]]
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".")
    parser.add_argument("--fix-commit", action="store_true", help="the change is a reviewer's fix commit")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("target", help="BASE..TIP, or a SHA meaning SHA^..SHA")
    args = parser.parse_args(argv)
    try:
        result = estimate(args.repo, args.target, args.fix_commit)
    except EstimateError as exc:
        print(f"estimate_review_effort: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
