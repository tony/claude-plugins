---
name: tdd-fix
description: TDD bug-fix workflow — reproduce bugs as failing tests, find root cause, fix, and verify. Use when asked to fix a bug using TDD methodology.
---

# TDD Bug-Fix Workflow

Perform a disciplined TDD bug-fix loop. Follow this workflow precisely for every bug.

---

## Phase 1: Understand the Bug

**Goal**: Parse the bug report into a testable reproduction scenario.

**Actions**:
1. Track progress through all phases
2. Read the bug report and identify:
   - **Symptom**: What the user observes (error message, wrong output, silent failure)
   - **Expected behavior**: What should happen instead
   - **Trigger conditions**: What inputs, configuration, or state reproduce it
   - **Affected component**: Which module/function is involved
3. **Read AGENTS.md / CLAUDE.md** to understand:
   - Test conventions (test structure, fixture patterns, assertion style)
   - Quality gate commands (test runner, linter, formatter, type checker)
   - Commit message format
4. Search the codebase to find the relevant source code and existing tests:
   - The test file that covers this area
   - The source file with the suspected bug
   - Any existing fixtures that can help reproduce the scenario
5. Read the identified files to understand current behavior
6. Summarize the understanding of the bug and confirm with user before proceeding

---

## Phase 2: Write a Failing Test (xfail)

**Goal**: Create a test that reproduces the bug and is expected to fail.

**CRITICAL**: Follow the project's test conventions from AGENTS.md / CLAUDE.md strictly. Read existing test files to understand patterns before writing any test code.

### xfail mechanism by framework

Use the appropriate "expected failure" mechanism for the project's test framework:

| Framework | xfail mechanism | Expected behavior on fix |
|-----------|----------------|--------------------------|
| pytest | `@pytest.mark.xfail(strict=True)` | XPASS (unexpected pass) when bug is fixed |
| Jest | `it.failing('...')` or `.todo()` | Test passes when bug is fixed |
| Rust (`#[test]`) | `#[should_panic]` or conditional `#[ignore]` | Remove annotation when fixed |
| Go | `t.Skip("known bug: ...")` | Remove skip when fixed |
| Other | Use the framework's skip/pending/expected-failure mechanism | Remove when fixed |

**Actions**:
1. Identify which test file to add the test to
2. Study existing test patterns in that file (parameterized fixtures, assertion styles, imports)
3. Write a test function that:
   - Has a descriptive name reflecting the bug scenario
   - Has a comment or docstring explaining the bug
   - Uses existing fixtures wherever possible
   - Is marked as expected-to-fail using the appropriate mechanism above
   - Asserts the **correct** (expected) behavior, not the buggy behavior
4. Run the test to confirm it fails as expected:
   ```
   <project's test command> <test_file>::<test_name>
   ```
5. Run the full test file to ensure no other tests broke
6. Run the project's quality gates (linter, formatter, type checker) as defined in AGENTS.md / CLAUDE.md
7. **Commit the failing test** using the project's commit message format from AGENTS.md / CLAUDE.md. The commit should indicate this is an xfail test for a known bug.

---

## Phase 3: Find the Root Cause

**Goal**: Trace from symptom to the exact code that needs to change.

**Actions**:
1. Read the source code path exercised by the test
2. Add temporary debug logging if needed (but track it for cleanup)
3. Identify the root cause — the specific line(s) or logic gap
4. If the bug spans multiple packages (this project + a dependency):
   - Note which package each change belongs to
   - Ensure the dependency is installed from local source for development (not a published version)
   - Verify by checking that the dependency's module files point to the local source directory rather than a package cache
5. Document the root cause clearly

---

## Phase 4: Fix the Bug

**Goal**: Apply the minimal fix that makes the test pass.

**Principles**:
- Minimal change — only fix what's broken
- Don't refactor surrounding code
- Don't add features beyond the fix
- Follow existing code patterns and style from AGENTS.md / CLAUDE.md

**Actions**:
1. Apply the fix to the source code
2. Remove any debug instrumentation added in Phase 3
3. Run the failing test — it should now trigger the xfail mechanism's "unexpected pass" behavior (e.g., XPASS in pytest), confirming the fix works
4. Run the project's quality gates as defined in AGENTS.md / CLAUDE.md
5. **Commit the fix** using the project's commit message format from AGENTS.md / CLAUDE.md. Include the root cause explanation.

---

## Phase 5: Remove xfail and Verify

**Goal**: Confirm the fix works and the test is a proper regression test.

**Actions**:
1. Remove the expected-failure marker from the test (e.g., `@pytest.mark.xfail`, `it.failing`, `#[should_panic]`, `t.Skip`)
2. Update the test comment/docstring to describe it as a regression test (not a bug report)
3. Run the test — it MUST pass
4. Run the full test suite for the affected file/module
5. Run all project quality gates as defined in AGENTS.md / CLAUDE.md
6. If ALL checks pass, **commit** using the project's commit message format. The commit should indicate the xfail is removed because the fix is verified.

---

## Phase 6: Recovery Loop (if fix doesn't work)

**Goal**: If the test still fails after the fix, diagnose why.

**Decision tree**:

### A. Is the reproduction genuine?
1. Read the test carefully — does it actually reproduce the reported bug?
2. Run the test with verbose output and examine the result
3. If the test is testing the wrong thing:
   - Go back to **Phase 2** and rewrite the test
   - Recommit with a corrected failing test

### B. Is the fix correct?
1. Add debug logging to trace execution through the fix
2. Check if the fix is actually being executed — stale builds or cached installs can cause the installed code to differ from source:
   - Verify the module file paths point to local source, not a package cache
   - If stale, rebuild or reinstall the dependency from local source
3. If the fix is wrong:
   - Revert the fix
   - Go back to **Phase 3** to re-analyze the root cause
   - Apply a new fix in **Phase 4**

### C. Loop limit
- After 3 failed fix attempts, stop and present findings to the user:
  - What was tried
  - What the debug output shows
  - What the suspected issue is
  - Ask for guidance

---

## Cross-Dependency Workflow

When the bug involves both this project and a dependency:

1. **Dependency changes first**: Fix the underlying library
2. **Commit in the dependency**: Use the dependency's commit conventions
3. **Verify dependency tests**: Run the dependency's test suite
4. **Update this project's dependency reference**: Ensure this project uses the fixed dependency from local source
5. **Then fix/test in this project**

**IMPORTANT**: Package managers that enforce lockfiles may overwrite local development installs. When developing across repos simultaneously, configure the package manager to use the local dependency path (e.g., path-based dependency sources, workspace links, or local overrides depending on the ecosystem).

---

## Quality Gates (every commit must pass)

Before EVERY commit, run the project's quality gates as defined in AGENTS.md / CLAUDE.md. Common gates include:

| Gate | Example commands |
|------|-----------------|
| Formatter | `ruff format`, `prettier --write`, `rustfmt`, `gofmt` |
| Linter | `ruff check`, `eslint`, `clippy`, `golangci-lint` |
| Type checker | `mypy`, `tsc --noEmit`, `basedpyright` |
| Tests | `pytest`, `jest`, `cargo test`, `go test` |

ALL gates must pass. A commit with failing tests or lint errors is not acceptable.

---

## Commit Message Format

Use the project's commit message format from AGENTS.md / CLAUDE.md. If no format is specified, use a conventional format that clearly describes:
- The component affected
- Whether this is a test addition, a fix, or xfail removal
- Why the change was needed
- What specifically changed
