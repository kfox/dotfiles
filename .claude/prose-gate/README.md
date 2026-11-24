# prose-gate

Two write-time checks that keep prose from becoming review surface.

The reasoning is in `~/.claude/CLAUDE.md` ("Prose is not review surface") and in
`~/.claude/skills/pairing-with-the-future/SKILL.md`. The short version: a prose
finding is the cheapest finding a reviewer can produce, and the fix for one is
more prose, which carries new claims, which yields new findings. That loop has no
fixed point, so prose gets checked here — deterministically, before the commit
exists — and not in review at all.

| Check | Stage | Refuses |
|---|---|---|
| `check_commit_message.py` | `commit-msg` | a subject over 80 characters, a body over 10 non-blank lines, or a body with no blank line after the subject |
| `lint_comments.py` | `pre-commit` | section banners, `TODO:`/`FIXME:`/`HACK:` markers, and commented-out code — among the lines the commit *adds* |

The caps are a policy choice: short enough to force a cut, loose enough that a
message saying what changed and why fits without a fight. On the repository they
were tuned against, messages authored one commit at a time ran a median of 8
non-blank body lines, so 10 binds occasionally rather than constantly.

## Install into a repository

Add to `.pre-commit-config.yaml`:

```yaml
default_install_hook_types: [pre-commit, commit-msg]
# Required. Without it every hook that does not restrict `stages` also runs at
# commit-msg against the message file, and `mixed-line-ending --fix=lf` rewrites
# it and fails.
default_stages: [pre-commit]

repos:
  - repo: local
    hooks:
      - id: commit-message-shape
        name: commit message shape
        entry: check-commit-message
        language: system
        stages: [commit-msg]
      - id: lint-comments
        name: comments this commit adds
        entry: lint-comments
        language: system
        types_or: [python, pyi]
```

Then `pre-commit install` — the `default_install_hook_types` line is what makes
a plain `install` wire the `commit-msg` hook as well as `pre-commit`. A repo that
was set up before this was added needs `pre-commit install` run again.

Both entries resolve through `~/.local/bin/`, which the wrappers live in.

## Tune per repository

```bash
git config prose.subjectMax 100     # default 80
git config prose.bodyMax 20         # default 10
git config prose.lintComments false # switch the comment linter off entirely
```

`git commit --no-verify` is the one-off bypass for both.

## What these deliberately do not check

Narration, self-justification and war stories — the judgment-heavy classes.
Lexical rules for them were measured against a 13,700-comment tree and matched
the legitimate categories (an upstream quirk, the provenance of a measured
constant, a cross-file contract) several times more often than the narration they
were aimed at. Those stay guidance, enforced by reading, because a hook that
cries wolf is a hook people learn to bypass.

The comment linter reads only the lines a diff adds, so `pre-commit run
--all-files` and CI have nothing staged to look at. That is deliberate: a comment
already in the tree is not the current commit's business.

## Tests

```bash
python3 ~/.claude/prose-gate/test_prose_gate.py
```

Nothing runs these automatically — they live outside any repository, so no CI
owns them. Run them after editing either script.
