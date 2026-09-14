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

Length is the lever. Say what the change does and the one or two facts that
make it the right change; stop there.

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
