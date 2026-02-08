# tdd

TDD bug-fix workflow — reproduce bugs as failing tests, find root cause, fix, and verify.

## Command

| Command | Description |
|---------|-------------|
| `/tdd:fix` | Run the full xfail-driven TDD bug-fix loop |

## 6-Phase Workflow

1. **Understand the bug** — Parse the report into symptom, expected behavior, trigger conditions
2. **Write a failing test** — Create an xfail-marked test that reproduces the bug
3. **Find root cause** — Trace from symptom to the exact code that needs to change
4. **Fix the bug** — Apply the minimal fix, confirm xfail flips to unexpected-pass
5. **Remove xfail and verify** — Convert to a regression test, run full quality gates
6. **Recovery loop** — If the fix doesn't work, diagnose and retry (up to 3 attempts)

Each phase produces a separate, atomic commit — the xfail test, the fix, and the xfail removal.

## Supported Test Frameworks

The command adapts to the project's test framework using the appropriate expected-failure mechanism:

| Framework | xfail mechanism |
|-----------|----------------|
| pytest (Python) | `@pytest.mark.xfail(strict=True)` |
| Jest (JavaScript/TypeScript) | `it.failing('...')` |
| Rust `#[test]` | `#[should_panic]` or `#[ignore]` |
| Go `testing` | `t.Skip("known bug: ...")` |

For other frameworks, the command uses whatever skip/pending/expected-failure mechanism is available.

## Quality Gate Discovery

The command reads AGENTS.md / CLAUDE.md to discover the project's quality gates (test runner, linter, formatter, type checker). All gates must pass before each commit.

## Cross-Dependency Bugs

When a bug spans this project and a dependency, the command handles both:
1. Fix the dependency first
2. Verify the dependency's tests pass
3. Configure the local dependency for development
4. Then fix and test in this project

## Prerequisites

- **git** — for atomic commits at each phase
- A test framework supported by the project
- Quality gate commands defined in AGENTS.md / CLAUDE.md

## Language-Agnostic Design

Test conventions, quality gates, and commit formats are all discovered from AGENTS.md / CLAUDE.md at runtime. The command works with any language or test framework.
