---
name: pairing-with-the-future
description: Coding guidelines for writing maintainable, human-readable code, based on Kelly Fox's "Pairing with the Future" presentation. Use when writing new code, refactoring existing code, reviewing code, or structuring projects, files, functions, tests, or comments.
---

# Pairing with the Future — Maintainable Code Guidelines

Code is communication across time and space. Write code for humans first, machines second — someone new to the codebase (or you, six months from now) must be able to read and understand it. Ease of change directly correlates with ease of understanding. These are suggestions, not rules; apply them with judgment.

## Project organization

- Follow the conventions of the language or framework.
- Arrange folders intuitively, from abstract to specific.
- Organize code by features or functionality.
- Keep related files and code close together.

## File layout

Order the contents of a file as:

1. Imports — built-in, then external, then internal, with each section alphabetized
2. Variables common to the entire file
3. Function and class definitions, before use
4. Main program logic
5. Exports

## Function and method structure

Order the contents of a function as:

1. Variable declarations and assignments
2. Early returns (if needed)
3. Core function logic
4. Return statement/value

Use single blank lines to separate sections or logical chunks of code.

## Writing good functions

- Each function should focus on accomplishing one task.
- Return early to avoid unnecessary processing.
- Don't bury a function's primary behavior inside an if/then statement.
- Write short functions — easier to read, reuse, review, adapt, and test. Don't be afraid of one-line functions.
- When possible, avoid sharing state with other functions, changing state, and side effects.

## Sizing guidelines

These are soft targets, not hard limits. The goal is to be concise and efficient with code, treating it as consumable, readable information for a human. Calibrate to the verbosity of the language — e.g. Go's inescapable error-handling boilerplate naturally lengthens functions, and that's fine.

| Item | Target |
|------|--------|
| Line length | 80–120 characters |
| Function arity | 3 arguments or fewer |
| Function length | Roughly 4–10 logical lines, excluding language-imposed boilerplate |
| Class | ~2 pages |
| File | ~3 pages |
| Files in a folder | Minimal scrolling |

If a function needs more than 3 arguments, pass an "options" object as the last argument — this lets the argument list grow without refactoring every call site.

## Naming

- Pick obvious names representative of the value or behavior.
- Choose names that make the code read like a narrative.
- Use long names when appropriate — unique names are easier to search for.
- Define all magic numbers and strings as named constants (e.g. `NUMBER_OF_SECONDS_IN_A_DAY` instead of `86400`).
- Check for namespace collisions — will the name be confused with an existing one?

## What prose may claim

Every sentence a project carries — a comment, a docstring, a commit message, a
changelog entry, a design note, a PR body, a review record — is read as fact by
someone who cannot check it cheaply. So the test for writing one is not whether
it is true. It is whether it informs.

**A sentence whose function is reassurance rather than information does not get
written.** Not "verify it first" — don't write it. The information-bearing
sentence is usually the first one; what follows is a change defending itself to
nobody.

The tells are absence, exhaustiveness and bounds: "holds back no other X", "the
whole of the difference", "has nothing further to say", "so that is all it can
expose", "either alone is insufficient", "every other caller". None of them is
checkable from where it gets written, which is why each costs one review round
to find and a second to fix — and the fix is a fresh unverified claim, so the
rounds do not converge.

When a claim about absence or bounds is load-bearing, it arrives as executed
evidence — a recorded search and its result, a mutation with a named victim —
or it is cut. Cut by preference. A change that needs a paragraph of defense
either is not ready or did not need the paragraph.

**Do not quantify what the change does not turn on.** The same rule, applied to
arithmetic. Most counts in prose are incidental — "prevents three errors",
"used by four callers", "the second of two passes" — and each is a place to be
wrong, goes stale the moment someone adds a fifth caller, and costs a review
round that fixes nothing about the code. Reach in this order:

1. **Cut the sentence.** An incidental count usually sits in a sentence that
   was reassurance to begin with. The stale number is the symptom; the sentence
   is the problem.
2. **Drop the count and keep the sentence**, where it earns its place.
   "Several", "a few", "most" carry the meaning and cannot rot. Better still,
   name the things instead of counting them: "the `--force` and `--dry-run`
   paths" survives a third path arriving, where "both paths" does not.
3. **Keep the exact number only when it is the information** — a measured
   constant with its provenance, a pinned version, an exit code, a boundary the
   code enforces — and then make it checkable. If the change turns on the
   number, say it exactly and say what produced it.

This holds for a comment, a commit message, a PR body and a review record
alike. A count you executed and recorded is evidence; a count you reached for
while describing the work is an unforced hostage to the next edit.

**Do not state precision the change does not turn on.** The same rule past
arithmetic. "The gate is retired", "the gate is not wired up", "its hooks are
gone from the settings file" and "the tool is no longer installed" are four
precisions of one fact; a change that removes the gate's documentation turns on
none of them, and only the coarsest survives someone deleting a binary.
Precision is a promise about the world, and the world moves.

The check is mechanical. A claim about the diff in front of you is cheap to
settle — the diff is right there. Every claim about something *outside* the diff
is a liability priced at one review round. Mark those sentences, then coarsen or
cut them: state the outside fact once, at the vaguest wording that still
explains the change, and never elaborate it.

## Code comments

The code is the narrative. A comment earns its place only when the code cannot
be made to say the same thing through naming, a smaller function, or an
extracted abstraction. Prose that restates the code is worse than nothing: it
doubles the reading cost, it rots into a lie the moment the code moves, and the
mismatch becomes review churn that fixes nothing real.

Keep only:

- **API documentation** — docstrings, Javadoc, JSDoc, Swagger. A module
  docstring is a concise description of what the module is and does, or a
  reference for its API. Not an essay defending it.
- **Tool directives** — `# type: ignore`, `# noqa`, `# pragma`, `# pyright:`,
  `# fmt: off`, `eslint-disable`, `#:schema`, a shebang, a `# vX.Y.Z` annotation
  a bot reads.
- **What the reader cannot reconstruct from the tree** — an upstream bug or
  deprecation (link it), a hardware or external-system quirk, the provenance of
  a measured constant, a cross-file contract stated at the line someone would
  edit. One line where one line will do.
- **Flow or data handling in code samples**, where illustrating is the point.

Never:

- **Narration** — describing what the next line does.
- **Self-justification** — "deliberately not X", "this is safe because",
  asserted invariants, arguing with an imagined reviewer, defending a choice
  the code does not make look arbitrary or extraneous.
- **War stories** — what an earlier version did and why it was replaced.
- **Section banners and step numbering** — `# --- helpers ---`, `# Step 1:`.
- **Describing complex functionality** — refactor instead.
- **Disabling code**, except for temporary local debugging.
- **Code kept "just in case"** — delete it; version control remembers.
- **TODOs and future work** — use the issue tracker.

The *why* behind a design belongs in the commit message and in the project's
design notes, not in the source. When a comment feels necessary, reach first for
a better name, a smaller function without side effects, or a named constant.

Three of those "never" classes are checked mechanically where the prose-gate
comment linter is installed — section banners, `TODO:`/`FIXME:` markers, and
commented-out code — and only against the comments a diff *adds*, never the file
around them. The rest stay judgment on
purpose: lexical rules for war stories and self-justification were measured
against a real tree and flagged legitimate provenance and hardware-quirk
comments far more often than the narration they were aimed at, which would make
the hook a nuisance and teach people to bypass it.

## Commit messages

The rule above displaces the *why* into the commit message. That is the right
destination, but it moves the rot rather than removing it unless the message is
held to the same standard — and a message is read as fact, by reviewers and by
whoever runs `git log` in two years.

Every checkable claim in a message is a promise you ran something. A number, a
count, an enumeration, a causal "so", a flat "cannot" — each one is a place to
be wrong, and volume is the strongest predictor of how many are.

- **Prefer the artifact to the assertion.** Name the two versions rather than
  counting the releases between them; the reader can subtract, and a count only
  invites an argument about inclusive bounds that changes nothing.
- **Never write a closed list you did not generate.** "The whole X surface here
  is A, B and C" is a claim about absence, which is the expensive kind to check
  and the easy kind to get wrong. Write "including", or cut it.
- **Cut rather than repair.** When a reviewer disputes a sentence, first ask
  whether its paragraph is load-bearing. A paragraph justifying a change that
  justifies itself is pure surface area, and rewriting it preserves the
  exposure at the same size.
- **Do not say where the change landed.** The diff already says it, exactly,
  and `git show --stat` will still say it in two years. Restating a path, a
  symbol or a mechanism in prose duplicates that answer in the one place that
  cannot be corrected: rewording a pushed message changes the SHA, which
  invalidates every recorded review of that commit and of everything stacked on
  it. The sentence then stays true only if nothing later in the branch moves
  what it names — and on an unmerged branch the likeliest thing to move is the
  mechanism just written, replaced by a review that has not read it yet. Say
  what the change accomplishes; let the diff say where.

This is what makes a message stricter than a comment rather than merely as
strict. A stale comment is edited by the next person to notice it. A stale
message is kept, because the fix costs more than the defect. So the bar is not
whether a sentence is true while being typed; it is whether it survives the
rest of the branch. Treat every structural fact as provisional until merge.

Length is the lever. Say what the change does and the one or two facts that
make it the right change; stop there.

Where the prose-gate `commit-msg` hook is installed, length is enforced rather
than asked for: a subject over 80 characters, or a body over 10 non-blank lines,
is refused. Trailers do not count toward the body, and merge,
revert and `fixup!` messages are left alone. The numbers are a policy choice:
short enough to force a cut, loose enough that what changed and why still fits.
A repo tunes them with `git config prose.subjectMax` and
`git config prose.bodyMax`.

## Refactoring

Refactor for **DRY-ness**:
- Extract repeated patterns into helper functions.
- Define common constants in a shared file.
- Avoid over-generalizing functions, classes, or objects — prefer function composition, superclass inheritance, or partitioning objects.

Refactor for **simplicity**:
- Avoid nesting; extract nested code into separate functions.
- Avoid clever code — cleverness conceals functionality. Save it for high-performance needs or coding challenges.

Refactor for **clarity**:
- Limit functions to one purpose.
- Move transformational code into separate, meaningfully named functions.
- Replace magic numbers and strings with meaningful constants.
- Prefer more verbose code when it aids understanding without hurting performance.

Refactor for **testability**:
- Only export what needs to be tested.
- Don't (deeply) test third-party code.
- Get configuration out of the code — use a file, database, or environment variables.
- Use dependency injection to simplify testing of external services, varying environments, or complex objects.

## Safety nets

**Testing:**
- Good tests explain how the code should work without reading the code itself.
- Only test what needs testing — bad tests can do more harm than good.
- Run tests automatically on file save (watch mode) and in CI after every commit.

**Source control:**
- Work in a feature branch.
- Commit early and often, with meaningful commit messages.
- Squash changes before merging.

**Third-party APIs:**
- Wrap external services in generalized wrappers when they may need replacing later, so the underlying service can be swapped with minimal disruption.

**Documentation:**
- Provide instructions for installing, developing, testing, contributing to, and using the project.
- Clear code and tests reduce the need for extensive documentation; leverage tools to generate docs where possible.

## Tooling

When possible:

- Use linters (eslint, pylint, etc.) and formatters (Prettier, Black, gofmt, etc.) with repo-committed configs.
- Use EditorConfig and pre-commit hooks to enforce consistency.
- Leverage type-checking
- Containerize the development environment (Docker, devcontainer.json) when reproducibility across machines matters.
- Don't reinvent the wheel without a good reason, but don't assume a popular tool is the best fit either.
