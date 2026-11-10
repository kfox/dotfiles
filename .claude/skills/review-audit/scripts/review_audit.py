#!/usr/bin/env python3
"""Measure code review in one repository from its Claude Code transcripts.

Subcommands:
  scan      read the transcripts in a period and write the raw review data
  report    turn that data into metrics, a hand-check sample and a note draft
  note      check a filled-in draft and attach it as a git note to main
  last      print the period of the most recent audit note
  install-hook  install the pre-push guard that refuses notes naming machine paths

Everything except the note stays in the --out directory, which is scratch.
"""

import argparse
import collections
import json
import os
import random
import re
import stat
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notepaths import find_machine_paths  # noqa: E402

PROJECTS = Path.home() / ".claude" / "projects"
NOTES_REF = "review-audit"
HOOK_MARKER = "# review-audit notes guard"
PLACEHOLDER = "<fill in"
ISSUES_DISABLED = "has disabled issues"
ESCAPE_LABEL = "escaped-review"

LANES = {"auditor", "adversary", "steward", "pragmatist"}
REVIEW_SKILLS = {"code-review", "panel-review"}
REVIEW_HINT = re.compile(r"code-review|panel-review|\breview", re.I)
IMPLEMENTER_HINT = re.compile(
    r"\bimplement|investigat|\bfix (\w+ ){0,5}(issues?|bugs|defects|guards)\b|all the way to a PR"
    r"|open the PR|resolve a|merge conflict|\brebase\b|leftovers|\bfixer\b|integrator", re.I)
EFFORT_LINE = re.compile(r"^\W*Effort:\W*(low|medium|high|xhigh|max)\b", re.M | re.I)
EFFORT_BEFORE_SHA = re.compile(r"\b(low|medium|high|xhigh|max)\s+`?([0-9a-f]{7,40})", re.I)
TARGET_LINE = re.compile(r"^\W*Target:\W*([0-9a-f]{7,40}(?:\.\.\.?[0-9a-f]{7,40})?)", re.M)
SHA = re.compile(r"\b[0-9a-f]{7,40}\b")
FIX_LINE = re.compile(r"^\W*Fix commit:\W*([0-9a-f]{7,40})", re.M | re.I)
FIX_LOOSE = re.compile(r"(?:(?<!\bno )fix(?:ed)?(?:[^\w.\n]+\w+){0,6}?[^\w.\n]{1,40}?"
                       r"|(?:new commit|own commit|commits?)\W{0,40}?\**`?)([0-9a-f]{7,12})\b", re.I)
HAS_DIGIT = re.compile(r"\d")
SECTION_HEAD = re.compile(r"^#{2,4}\s*(Fixed|Advisory|Declined|Outside this change|Checked clean)\b", re.I)
EMPTY_BULLET = re.compile(r"^-\s*(\(?none\)?\.?|—|-)?\s*$", re.I)
JSON_FINDINGS = re.compile(r"```json\s*(\[.*?\])\s*```", re.S)
PROSE_FINDING = re.compile(r"^\W*Finding(?!s)\b.*$", re.M | re.I)
PROSE_FIXED = re.compile(r"(?<!not )\bfixed\b", re.I)
PROSE_CLEAN = re.compile(r"found no (?:\w+ )?defects|found nothing to fix|\bno findings\b|Findings:\W*none"
                         r"|neither \w+ has an? (?:\w+ )?defect", re.I)
REVIEW_REQUEST = re.compile(r"^\W*(?:\w+ separate )?code reviews?\b|^\W*review (?:of )?(?:commit|PR\b|pull request"
                            r"|#?\d+\b|[0-9a-f]{7,40}\b)", re.I)
EFFORT_WORDS = re.compile(r"\b(low|medium|high|xhigh|max)[ -]effort\b", re.I)
ABSOLUTE_PATH = re.compile(r"(?<![\w.])/[^\s`'\"),;]+")


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def main_checkout(repo):
    common = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    return common.parent if common.name == ".git" else common


def project_dirs(checkout, extra):
    key = re.sub(r"[^A-Za-z0-9]", "-", str(checkout))
    dirs = [PROJECTS / key, *sorted(PROJECTS.glob(key + "--claude-worktrees-*"))]
    dirs += [Path(d).expanduser() for d in extra]
    return [d for d in dirs if d.is_dir()]


def parse_time(stamp):
    if not stamp:
        return None
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()


def day_start(day):
    return datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc).timestamp()


def blocks(content):
    return [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []


def text_of(content):
    if isinstance(content, str):
        return content
    return "\n".join(b.get("text", "") for b in blocks(content) if b.get("type") == "text")


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def transcript_lines(path):
    with open(path, "rb") as handle:
        for line in handle:
            try:
                yield json.loads(line)
            except ValueError:
                continue


def scan_transcript(path):
    usage, pending, skill_calls = {}, {}, []
    first = last = prompt = final = None
    audits_itself = False
    for entry in transcript_lines(path):
        when = parse_time(entry.get("timestamp"))
        if when is not None:
            first = when if first is None else min(first, when)
            last = when if last is None else max(last, when)
        message = entry.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if entry.get("type") == "assistant":
            if message.get("usage"):
                usage[message.get("id") or len(usage)] = message["usage"]
            for block in blocks(content):
                if block.get("type") == "text" and block.get("text", "").strip():
                    final = block["text"]
                elif block.get("type") == "tool_use":
                    name, args = block.get("name"), block.get("input") or {}
                    skill = str(args.get("skill", "")).split(":")[-1]
                    if name == "SubagentHandback":
                        final = str(args.get("message", ""))
                    elif name == "Skill" and skill == "review-audit":
                        audits_itself = True
                    elif name == "Skill" and skill in REVIEW_SKILLS:
                        call = {"skill": skill, "args": str(args.get("args", ""))[:2000],
                                "t0": when, "t1": None, "result": ""}
                        skill_calls.append(call)
                        pending[block.get("id")] = call
        elif entry.get("type") == "user":
            text = text_of(content)
            if "<command-name>/review-audit" in text:
                audits_itself = True
            if prompt is None and text.strip():
                prompt = text
            for block in blocks(content):
                if block.get("type") == "tool_result" and block.get("tool_use_id") in pending:
                    call = pending.pop(block["tool_use_id"])
                    call["t1"] = when
                    call["result"] = text_of(block.get("content"))[:8000]
    tokens = sum((u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
                 + (u.get("cache_read_input_tokens") or 0) + (u.get("output_tokens") or 0)
                 for u in usage.values())
    return {"tokens": tokens, "t0": first, "t1": last, "prompt": (prompt or "")[:4000],
            "final": (final or "")[:8000], "skill_calls": skill_calls, "audits_itself": audits_itself}


def classify(meta, forked, prompt, reviewer_types, extra_kinds):
    skill = forked.get("skillName")
    if skill in REVIEW_SKILLS:
        return f"{skill}:{forked.get('effort') or 'unstated'}"
    agent_type = meta.get("agentType")
    if agent_type in LANES:
        return f"lane:{agent_type}"
    if agent_type == "reviewer" or agent_type in reviewer_types:
        effort = EFFORT_LINE.search(prompt)
        return f"{agent_type}:{effort.group(1).lower() if effort else 'unstated'}"
    if prompt.startswith("Review target:"):
        return "code-review:internal"
    if REVIEW_REQUEST.search(prompt[:300]):
        effort = EFFORT_LINE.search(prompt) or EFFORT_WORDS.search(prompt[:1500])
        return f"prompted:{effort.group(1).lower() if effort else 'unstated'}"
    head = ((meta.get("description") or "") + " " + prompt)[:600]
    for name, pattern in extra_kinds:
        if pattern.search(head):
            return name
    return None


def names_other_checkout(prompt, checkout):
    here, siblings = str(checkout).rstrip("/"), str(checkout.parent).rstrip("/") + "/"
    first = next((p for p in ABSOLUTE_PATH.findall(prompt[:4000]) if p.startswith(siblings)), None)
    return first is not None and first != here and not first.startswith(here + "/")


def mark_wrappers(agents):
    review_parents = {a["meta"].get("parentAgentId") for a in agents
                      if (a["kind"] or "").split(":")[0] in REVIEW_SKILLS}
    for agent in agents:
        runs_review = agent["skill_calls"] or agent["id"] in review_parents
        head = ((agent["meta"].get("description") or "") + " " + agent["prompt"])[:600]
        if (agent["kind"] is None and runs_review and REVIEW_HINT.search(head)
                and not IMPLEMENTER_HINT.search(head[:500])):
            agent["kind"] = "wrapper"


def extra_kind(spec):
    name, sep, pattern = spec.partition("=")
    if not sep or not name:
        raise argparse.ArgumentTypeError("expected NAME=REGEX")
    return name, re.compile(pattern, re.I)


def scan(args):
    checkout = main_checkout(args.repo)
    dirs = project_dirs(checkout, args.extra_project_dir)
    since = day_start(args.since)
    until = day_start(args.until + timedelta(days=1))
    sessions = []
    for directory in dirs:
        for main in sorted(directory.glob("*.jsonl")):
            session = scan_transcript(main)
            if session["t0"] is None or not since <= session["t0"] < until or session["audits_itself"]:
                continue
            session["id"] = main.stem
            session["agents"] = []
            for path in sorted((directory / main.stem / "subagents").glob("*.jsonl")):
                agent = scan_transcript(path)
                agent["id"] = path.stem.removeprefix("agent-")
                agent["meta"] = read_json(path.with_suffix(".meta.json"))
                forked = read_json(path.with_suffix(".forked-skill.json"))
                agent["kind"] = classify(agent["meta"], forked, agent["prompt"],
                                         set(args.reviewer_type), args.extra_kind)
                if agent["kind"] and names_other_checkout(agent["prompt"], checkout):
                    agent["kind"] = None
                agent["description"] = agent["meta"].get("description") or ""
                session["agents"].append(agent)
            mark_wrappers(session["agents"])
            sessions.append(session)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    period = {"since": args.since.isoformat(), "until": args.until.isoformat()}
    (out / "scan.json").write_text(json.dumps({"period": period, "sessions": sessions}))
    print(f"{len(sessions)} sessions, {sum(len(s['agents']) for s in sessions)} subagents "
          f"from {len(dirs)} project directories -> {out / 'scan.json'}")


def parse_report(text, target, reviewed=()):
    sections, fixed = collections.Counter(), []
    current = None
    for line in text.splitlines():
        head = SECTION_HEAD.match(line)
        if head:
            current = head.group(1).lower()
            continue
        if line.startswith("#"):
            current = None
            continue
        bullet = line.rstrip()
        if current and bullet.startswith("- ") and not EMPTY_BULLET.match(bullet):
            sections[current] += 1
            if current == "fixed":
                fixed.append(bullet[2:])
    for block in JSON_FINDINGS.findall(text):
        try:
            findings = json.loads(block)
        except ValueError:
            continue
        sections["reported"] += len(findings)
    for line in PROSE_FINDING.findall(text):
        if PROSE_FIXED.search(line):
            sections["fixed"] += 1
            fixed.append(line.strip())
        else:
            sections["reported"] += 1
    if not sections and PROSE_CLEAN.search(text):
        sections["clean verdict"] += 1
    fix = FIX_LINE.search(text)
    fix_sha = fix.group(1)[:7] if fix else None
    if fix_sha is None:
        skip = {s[:7] for s in (target, *reviewed) if s}
        loose = [s[:7] for s in FIX_LOOSE.findall(text.split("```json")[0])
                 if s[:7] not in skip and HAS_DIGIT.search(s)]
        fix_sha = loose[0] if loose else None
    return sections, fixed, fix_sha


def target_of(agent):
    source = agent["description"] + "\n" + agent["prompt"][:1500]
    for pattern, group in ((TARGET_LINE, 1), (EFFORT_BEFORE_SHA, 2), (SHA, 0)):
        match = pattern.search(source)
        if match:
            return match.group(group)
    return None


def endpoints(target):
    return [part[:7] for part in re.split(r"\.\.\.?", target or "") if part]


def review_units(session):
    by_id = {a["id"]: a for a in session["agents"]}

    def review_ancestor(agent):
        parent, hops = agent["meta"].get("parentAgentId"), 0
        while parent in by_id and hops < 20:
            if by_id[parent]["kind"]:
                return by_id[parent]
            parent, hops = by_id[parent]["meta"].get("parentAgentId"), hops + 1
        return None

    children = collections.defaultdict(list)
    for agent in session["agents"]:
        children[agent["meta"].get("parentAgentId")].append(agent)

    def subtree_tokens(agent):
        return agent["tokens"] + sum(subtree_tokens(c) for c in children.get(agent["id"], []))

    review_tokens = sum(a["tokens"] for a in session["agents"] if a["kind"] or review_ancestor(a))
    units = []
    for agent in session["agents"]:
        if not agent["kind"] or review_ancestor(agent):
            continue
        target = target_of(agent)
        reviewed = SHA.findall(agent["description"] + "\n" + agent["prompt"][:4000])
        sections, fixed, fix_sha = parse_report(agent["final"], target, reviewed)
        units.append({"session": session["id"], "kind": agent["kind"], "target": target,
                      "t0": agent["t0"], "tokens": subtree_tokens(agent), "sections": sections,
                      "fixed": fixed, "fix": fix_sha})
    return units, review_tokens


def chain_depths(units):
    depths = collections.Counter()
    reviews_of_fixes = 0
    by_session = collections.defaultdict(list)
    for unit in units:
        by_session[unit["session"]].append(unit)
    for runs in by_session.values():
        runs.sort(key=lambda u: u["t0"] or 0)
        depth, root = {}, {}
        for i, unit in enumerate(runs):
            depth[i], root[i] = 1, i
            for j in range(i):
                fix = runs[j]["fix"]
                if fix and any(e.startswith(fix) or fix.startswith(e) for e in endpoints(unit["target"])):
                    if depth[j] + 1 > depth[i]:
                        depth[i], root[i] = depth[j] + 1, root[j]
            if depth[i] > 1:
                reviews_of_fixes += 1
        deepest = collections.defaultdict(int)
        for i in depth:
            deepest[root[i]] = max(deepest[root[i]], depth[i])
        depths.update(deepest.values())
    return dict(sorted(depths.items())), reviews_of_fixes


def inline_calls(session):
    calls = list(session["skill_calls"])
    for agent in session["agents"]:
        calls += agent["skill_calls"]
    return sum(1 for c in calls if c["result"].startswith(f'Skill "{c["skill"]}" completed'))


def kind_group(kind):
    return kind.split(":")[0] if kind.startswith("lane:") else kind


def has_escape_label(checkout):
    listed = subprocess.run(["gh", "label", "list", "--search", ESCAPE_LABEL, "--limit", "100", "--json", "name"],
                            cwd=checkout, check=True, capture_output=True, text=True).stdout
    return any(item["name"] == ESCAPE_LABEL for item in json.loads(listed))


def escapes(checkout, period):
    if not has_escape_label(checkout):
        print(f"the repository has no {ESCAPE_LABEL} label, so escapes were not collected", file=sys.stderr)
        return None
    numbers = set()
    for kind in ("issue", "pr"):
        try:
            listed = subprocess.run(
                ["gh", kind, "list", "--label", ESCAPE_LABEL, "--state", "all", "--limit", "500",
                 "--search", f"created:{period['since']}..{period['until']}", "--json", "number"],
                cwd=checkout, check=True, capture_output=True, text=True).stdout
        except subprocess.CalledProcessError as failed:
            if kind == "issue" and ISSUES_DISABLED in (failed.stderr or ""):
                continue
            raise
        numbers.update(item["number"] for item in json.loads(listed))
    return sorted(numbers)


def short(count):
    for size, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if count >= size:
            return f"{count / size:.1f}{suffix}"
    return str(count)


def report(args):
    out = Path(args.out)
    data = json.loads((out / "scan.json").read_text())
    period, sessions = data["period"], data["sessions"]
    units, review_tokens = [], 0
    for session in sessions:
        found, tokens = review_units(session)
        units += found
        review_tokens += tokens
    total = sum(s["tokens"] + sum(a["tokens"] for a in s["agents"]) for s in sessions)
    by_kind = collections.defaultdict(lambda: [0, 0])
    for unit in units:
        by_kind[kind_group(unit["kind"])][0] += 1
        by_kind[kind_group(unit["kind"])][1] += unit["tokens"]
    findings = collections.Counter()
    for unit in units:
        findings.update(unit["sections"])
    depths, reviews_of_fixes = chain_depths(units)
    metrics = {
        "period": period,
        "sessions": len(sessions),
        "subagents": sum(len(s["agents"]) for s in sessions),
        "tokens": {"total": total, "review": review_tokens,
                   "review_share": round(review_tokens / total, 4) if total else 0},
        "reviews": {kind: {"count": c, "tokens": t} for kind, (c, t) in sorted(by_kind.items())},
        "inline_review_skill_calls": sum(inline_calls(s) for s in sessions),
        "findings": dict(findings),
        "reviews_with_fix_commit": sum(1 for u in units if u["fix"]),
        "reviews_clean": sum(1 for u in units if u["sections"] and not u["sections"]["fixed"]
                             and not u["sections"]["reported"]),
        "reviews_unparsed": sum(1 for u in units if not u["sections"]),
        "chain_depths": depths,
        "reviews_of_fix_commits": reviews_of_fixes,
        "escaped_review_issues": None if args.no_escapes else escapes(main_checkout(args.repo), period),
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2))

    pool = [(u["target"], u["fix"], line) for u in units for line in u["fixed"]]
    sample = random.Random(args.seed).sample(pool, min(args.sample, len(pool)))
    (out / "sample.md").write_text(
        "# Hand-check sample\n\nSort each into defect, contract or not a finding; "
        "the fix commit settles a doubtful one.\n\n"
        + "".join(f"- [ ] target {t} fix {f}: {line}\n" for t, f, line in sample))

    (out / "note-draft.md").write_text(note_draft(metrics, len(sample)))
    print(json.dumps(metrics, indent=2))
    print(f"\nsample: {out / 'sample.md'} ({len(sample)} of {len(pool)} fixed findings)")
    print(f"draft:  {out / 'note-draft.md'}")


def note_draft(metrics, sampled):
    tokens = metrics["tokens"]
    lines = [
        f"review-audit {metrics['period']['until']}",
        f"since: {metrics['period']['since']}",
        f"until: {metrics['period']['until']}",
        "",
        f"sessions: {metrics['sessions']} (subagents: {metrics['subagents']})",
        f"tokens: {short(tokens['total'])} total, {short(tokens['review'])} review "
        f"({100 * tokens['review_share']:.1f}%)",
        "reviews by kind:",
        *(f"  {kind}: {v['count']} reviews, {short(v['tokens'])}" for kind, v in metrics["reviews"].items()),
        f"inline review skill calls: {metrics['inline_review_skill_calls']}",
        "report bullets: " + ", ".join(f"{n} {k}" for k, n in sorted(metrics["findings"].items())),
        f"reviews with a fix commit: {metrics['reviews_with_fix_commit']}; clean: {metrics['reviews_clean']}; "
        f"report not parsed: {metrics['reviews_unparsed']}",
        "fix chain depths: " + ", ".join(f"depth {d}: {n}" for d, n in metrics["chain_depths"].items()),
        f"reviews of a fix commit: {metrics['reviews_of_fix_commits']}",
        "",
        f"sample of {sampled} fixed bullets: {PLACEHOLDER}: N defects, N contract, N not findings>",
        "escapes:",
    ]
    issues = metrics["escaped_review_issues"]
    if issues is None:
        lines.append(f"  {PLACEHOLDER}: escapes were not collected; list them or say why>")
    elif not issues:
        lines.append("  none")
    else:
        lines += [f"  #{n}: {PLACEHOLDER}: introduced by SHA (PR #N), review TIER, pinned yes/no, "
                  "in diff yes/no, needed hardware yes/no>" for n in issues]
    lines += ["", f"proposal: {PLACEHOLDER}: at most one policy change, or none>", ""]
    return "\n".join(lines)


def default_branch_tip(repo):
    for ref in ("refs/remotes/origin/HEAD", "refs/remotes/origin/main", "refs/heads/main"):
        try:
            return git(repo, "rev-parse", "--verify", ref + "^{commit}")
        except subprocess.CalledProcessError:
            continue
    raise SystemExit("cannot find the default branch: no origin/HEAD, origin/main or main")


def note(args):
    text = Path(args.file).read_text()
    problems = [f"{rule}: {token}" for rule, token in find_machine_paths(text)]
    if PLACEHOLDER in text:
        problems.append(f"an unfilled '{PLACEHOLDER} ...>' placeholder remains")
    if problems:
        raise SystemExit("refusing the note:\n  " + "\n  ".join(problems))
    commit = args.commit or default_branch_tip(args.repo)
    flags = ["-f"] if args.force else []
    git(args.repo, "notes", f"--ref={NOTES_REF}", "add", *flags, "-F", str(Path(args.file).resolve()), commit)
    print(f"note added to {commit[:12]} under refs/notes/{NOTES_REF}; it stays in this clone")


def last(args):
    listing = git(args.repo, "notes", f"--ref={NOTES_REF}", "list")
    latest = None
    for line in listing.splitlines():
        blob, commit = line.split()
        text = git(args.repo, "cat-file", "blob", blob)
        until = re.search(r"^until:\s*(\d{4}-\d{2}-\d{2})", text, re.M)
        if until and (latest is None or until.group(1) > latest[0]):
            latest = (until.group(1), commit)
    if latest is None:
        print("no audit notes yet")
        return
    print(f"until: {latest[0]} on {latest[1][:12]}")
    print(f"next --since: {date.fromisoformat(latest[0]) + timedelta(days=1)}")


HOOK = """#!/bin/sh
{marker}
input=$(cat)
case "$input" in
*refs/notes/*)
    printf '%s\\n' "$input" | python3 "{guard}" || exit 1
    ;;
esac
if [ -x "$0.local" ]; then
    printf '%s\\n' "$input" | "$0.local" "$@" || exit 1
fi
"""


def install_hook(args):
    hooks_path = subprocess.run(["git", "-C", str(args.repo), "config", "core.hooksPath"],
                                capture_output=True, text=True).stdout.strip()
    if hooks_path:
        raise SystemExit(f"core.hooksPath is set to {hooks_path}; add the guard to that hook manager "
                         f"instead: pipe pre-push stdin to {Path(__file__).with_name('check_notes_push.py')}")
    hooks = Path(git(args.repo, "rev-parse", "--path-format=absolute", "--git-path", "hooks"))
    hooks.mkdir(exist_ok=True)
    hook, chained = hooks / "pre-push", hooks / "pre-push.local"
    if hook.exists() and HOOK_MARKER not in hook.read_text():
        if chained.exists():
            raise SystemExit(f"both {hook} and {chained} exist; merge them by hand first")
        hook.rename(chained)
        print(f"moved the existing pre-push hook to {chained}; the guard runs it after itself")
    guard = Path(__file__).resolve().with_name("check_notes_push.py")
    hook.write_text(HOOK.format(marker=HOOK_MARKER, guard=guard))
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"installed {hook}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=os.getcwd(), help="any checkout or worktree of the repository")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("scan")
    p.add_argument("--since", type=date.fromisoformat, required=True)
    p.add_argument("--until", type=date.fromisoformat, default=date.today())
    p.add_argument("--out", required=True)
    p.add_argument("--extra-project-dir", action="append", default=[],
                   help="another ~/.claude/projects directory, e.g. from where the repo used to live")
    p.add_argument("--reviewer-type", action="append", default=[],
                   help="a project agent type to count as a single-pass reviewer")
    p.add_argument("--extra-kind", action="append", default=[], type=extra_kind, metavar="NAME=REGEX",
                   help="count an agent whose description or prompt opening matches REGEX as review work NAME")
    p.set_defaults(func=scan)

    p = sub.add_parser("report")
    p.add_argument("--out", required=True)
    p.add_argument("--sample", type=int, default=20)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--no-escapes", action="store_true", help="skip the GitHub escaped-review lookup")
    p.set_defaults(func=report)

    p = sub.add_parser("note")
    p.add_argument("--file", required=True)
    p.add_argument("--commit", help="default: the tip of origin's default branch")
    p.add_argument("--force", action="store_true", help="replace an existing note on that commit")
    p.set_defaults(func=note)

    sub.add_parser("last").set_defaults(func=last)
    sub.add_parser("install-hook").set_defaults(func=install_hook)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
