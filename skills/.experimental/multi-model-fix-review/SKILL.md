---
name: multi-model-fix-review
description: Fix multi-model review findings as atomic commits with test coverage. Use when review findings need to be validated, tested, and applied as fixes.
---

# Fix Review Findings

Process multi-model code review findings from the conversation context. Validate each finding independently against the actual codebase and project conventions, add test coverage where applicable, apply fixes as separate atomic commits, and ensure all quality gates pass before each commit.

Multi-pass (`multipass`, `x2`, etc.) is not applicable to this skill — it is already iterative by nature. Trigger words are ignored if present.

---

## Phase 1: Parse and Prioritize Findings

**Goal**: Extract structured findings from the multi-model review report in the conversation.

**Actions**:

1. **Locate the review report** in the conversation context (output from multi-model-review or similar)

2. **Extract each finding** into a numbered list with:
   - **Consensus level**: how many reviewers flagged it (3, 2, or 1)
   - **Severity**: Critical / Important / Suggestion (after consensus promotion)
   - **Reviewers**: which models flagged it (Claude, Gemini, GPT)
   - **File and line**: location in the codebase
   - **Description**: what the issue is
   - **Recommendation**: suggested fix

3. **Sort by priority** (process in this order):
   - Consensus Critical (3 reviewers) first
   - Consensus Critical (2 reviewers, promoted)
   - Consensus Important (2 reviewers, promoted)
   - Single-reviewer Important
   - Single-reviewer Suggestions

4. **Track progress** through each finding

5. **Read CLAUDE.md / AGENTS.md** for project conventions that apply to the fixes

---

## Phase 2: Validate Each Finding

**Goal**: Independently assess whether each finding is valid and actionable.

For EACH finding:

1. **Read the relevant code** — the exact lines referenced in the finding

2. **Check project conventions** — read CLAUDE.md/AGENTS.md to verify whether the finding aligns with project standards

3. **Review the project's own APIs** — read the function signatures, return types, and docstrings to understand the intended contract vs what the reviewers flagged

4. **Check existing test coverage** — search for tests that already cover this code path

5. **Assess validity** using these criteria:
   - **Valid**: The finding identifies a real issue that aligns with project conventions
   - **Already addressed**: The issue was already fixed in a later commit
   - **Incorrect**: The reviewer misread the code or the suggestion would introduce a bug
   - **Out of scope**: Valid concern but not related to this branch's changes
   - **Pre-existing**: Valid but existed before this branch (not introduced by our changes)

6. **Document the verdict** for each finding:
   - If valid: note the planned fix AND test coverage strategy
   - If invalid: note the specific reason (cite code, tests, or conventions)

7. **Present the validation results** to the user before making changes:
   - List each finding with its verdict
   - For valid findings, describe: the fix + the test approach
   - **Wait for user confirmation** before proceeding to Phase 3

---

## Phase 3: Apply Fixes (One Commit Per Finding)

**Goal**: Apply each valid finding as a separate, atomic commit with test coverage.

**CRITICAL**: Process one finding at a time. Complete the full cycle for each before moving to the next.

For EACH valid finding:

### Step 1: Search for Existing Test Coverage

Before writing any code, search for existing tests that can be extended:

- Search for the affected function/module name in the test directory
- Read the test file structure — identify existing parameterized fixtures
- Look for fixtures or helpers that can be extended with a new test case

**Priority order for test placement**:
1. **Extend existing parameterized test** — add a new entry to an existing fixture list
2. **Add a case to an existing test function** — if the test function already covers the component
3. **Create a new test function** in the existing test file — only if no existing test covers this area
4. **Create a new test file** — only as a last resort

### Step 2: Write/Extend Tests

Follow the project's test conventions from AGENTS.md/CLAUDE.md strictly. Common conventions to check for:

- Test structure (classes vs functions, parameterized vs individual)
- Fixture patterns (project-specific fixtures, setup/teardown)
- Assertion style (assert statements, matchers, custom assertions)
- Import conventions
- Mock patterns and documentation requirements

### Step 3: Apply the Fix

- Make the minimal change that addresses the finding
- Do not bundle unrelated changes
- Follow project conventions from CLAUDE.md/AGENTS.md

### Step 4: Run Quality Gates

Run the project's quality gates as defined in AGENTS.md/CLAUDE.md. All gates must pass before committing.

- If any gate fails, fix the issue before proceeding
- If a test fails due to the change, either:
  - Adjust the fix to be correct, OR
  - Update the test if the finding changes expected behavior
- ALL gates must pass before committing

### Step 5: Commit

Stage only the files changed for this specific finding:

```bash
git add <specific-files>
```

Use the project's commit message format from AGENTS.md/CLAUDE.md. Include a reference to the multi-model review finding.

### Step 6: Verify Clean State

After committing, confirm:
```bash
git status
```

```bash
git diff
```

No uncommitted changes should remain before moving to the next finding.

---

## Phase 4: Summary

After processing all valid findings, present a summary:

1. **Applied fixes**: List each committed fix with its commit hash and consensus level
2. **Tests added/extended**: List test coverage improvements per finding
3. **Skipped findings**: List each invalid/out-of-scope finding with the reason
4. **Final verification**: Run the full quality gate one last time
5. Report the final pass/fail status
6. Show the commit log for the session:
   ```bash
   git log --oneline -<N>
   ```

---

## Recovery: Quality Gate Failure

If quality gates fail after applying a fix:

1. **Identify** which gate failed and why
2. **Fix** the issue (adjust the change, not bypass the gate)
3. **Re-run** all gates
4. If the fix cannot be made to pass all gates after 2 attempts:
   - Revert the change: `git checkout -- <files>`
   - Mark the finding as "valid but could not apply cleanly"
   - Move to the next finding
   - Report the issue in the Phase 4 summary

---

## Rules

- Never skip quality gates
- Never bundle multiple findings into one commit
- Never modify code that isn't related to the finding being addressed
- Always wait for user confirmation after Phase 2 validation
- Always use the project's commit message conventions from AGENTS.md/CLAUDE.md
- Always search for existing tests before creating new test functions
- Always prefer extending existing test fixtures over creating new tests
- If a finding requires changes in multiple files, that is still ONE commit (one logical change)
- Process consensus findings before single-reviewer findings
- If a finding is pre-existing (not from this branch), note it but still fix if the user approved it
