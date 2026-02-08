---
description: Generate CHANGES entries from branch commits and PR context
argument-hint: "[optional additional context about the changes]"
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit"]
---

# Changelog Entry Generator

Generate well-formatted changelog entries from the current branch's commits and PR context. This command analyzes commits, categorizes them, and inserts entries into the changelog file after user review.

Additional context from user: $ARGUMENTS

---

## Phase 1: Gather Context

**Goal**: Collect all information needed to generate changelog entries.

**Actions**:

1. **Detect project name** — search for project metadata in order of precedence:
   - `pyproject.toml` → `[project] name`
   - `package.json` → `name`
   - `Cargo.toml` → `[package] name`
   - `go.mod` → module path (last segment)
   - Fall back to the repository directory name

2. **Detect trunk branch**:
   ```
   git symbolic-ref refs/remotes/origin/HEAD
   ```
   - Strip `refs/remotes/origin/` prefix to get branch name
   - Fall back to `master` if the above fails

3. **Verify not on trunk**:
   - Check current branch: `git branch --show-current`
   - If on trunk, report "Already on trunk branch — nothing to generate" and stop

4. **Find and read the changelog file** — scan the repo root for common changelog filenames:
   - `CHANGES`, `CHANGES.md`
   - `CHANGELOG`, `CHANGELOG.md`
   - `HISTORY`, `HISTORY.md`
   - `NEWS`, `NEWS.md`
   - If multiple exist, prefer the one with the most content
   - If none exist, report "No changelog file found" and ask the user which filename to create

5. **Analyze the changelog format**:
   - **Heading format**: Detect the pattern used for release headings (e.g., `## v1.2.3`, `## [1.2.3]`, `## project v1.2.3`, `## 1.2.3 (YYYY-MM-DD)`)
   - **Unreleased section**: Look for an "unreleased" heading or a placeholder comment (e.g., `<!-- END PLACEHOLDER`, `## [Unreleased]`, `## Unreleased`)
   - **Insertion point**: Determine where new entries go — after a placeholder comment, under an unreleased heading, or at the top of the file
   - **Section headings**: Note existing section headings (e.g., `### Bug fixes`, `### Features`) and their capitalization style
   - Record this format to match it exactly when generating entries

6. **Check for PR**:
   ```
   gh pr view --json number,title,body,labels 2>/dev/null
   ```
   - If a PR exists, extract the number, title, body, and labels
   - If no PR exists, note that `(#???)` placeholders will be used

7. **Get commits**:
   ```
   git log <trunk>..HEAD --oneline
   ```
   - Also get full commit details for body parsing:
   ```
   git log <trunk>..HEAD --format='%H %s%n%b---'
   ```
   - If no commits ahead of trunk, report "No commits ahead of trunk" and stop

---

## Phase 2: Categorize Commits

**Goal**: Parse commits into changelog categories and group related ones.

### Commit type mapping

Parse the commit type from the commit subject. Adapt to the project's commit convention (detected from AGENTS.md/CLAUDE.md or from existing commit history):

| Commit type | CHANGES section | Notes |
|---|---|---|
| `feat` | Features / New features | New functionality |
| `fix` | Bug fixes | Bug fixes |
| `docs` | Documentation | Doc changes |
| `test` | Tests | Test additions/changes |
| `refactor` | (only if user-visible) | Skip internal-only refactors |
| `chore`, `deps` | Development | Maintenance, dependency bumps |
| `style` | (skip) | Formatting-only changes |

### Grouping rules

- **TDD workflow sequences**: An xfail commit + a fix commit + an xfail-removal commit should collapse into a **single** bug fix entry. The fix commit's message is the primary source.
- **Dependency bumps**: A deps commit + a changelog doc commit = 1 entry under "Breaking changes" (if it's a minimum version bump) or "Development"
- **Multi-commit features**: Sequential `feat` commits on the same component collapse into one entry
- **Skip entirely**: merge commits, lock-only changes, internal-only refactors

### Output of this phase

A structured list of entries grouped by section, each with:
- Section name (e.g., "Bug fixes")
- Entry text (formatted markdown)
- Source commit(s) for traceability

---

## Phase 3: Generate Entries

**Goal**: Write the exact markdown to be inserted into the changelog.

### Format rules (derived from the existing changelog file)

1. **Section headings**: Match the style found in Phase 1 (e.g., `### Bug fixes`, `### Bug Fixes`)

2. **Section order** (only include sections that have entries):
   - Breaking changes
   - Features / New features
   - Bug fixes
   - Documentation
   - Tests
   - Development

3. **Simple entries** — single bullet:
   ```markdown
   - Brief description of the change (#123)
   ```

4. **Detailed entries** — sub-heading with description:
   ```markdown
   #### Component: Brief description (#123)

   Explanatory paragraph about what changed and why.

   - Bullet point with specific detail
   - Another detail
   ```

5. **PR references**:
   - If PR number is known: `(#512)`
   - If no PR exists: `(#???)`

6. **Match existing style**:
   - Check whether the project uses "Bug fixes" or "Bug Fixes" (match existing capitalization)
   - Check whether "Features" or "New features" is used
   - Match the heading level, bullet style, and overall format of existing entries
   - Preserve the project's conventions

### Entry writing guidelines

- Write from the user's perspective — what changed for them, not internal implementation details
- Lead with the *what*, not the *why* (the description paragraph handles *why*)
- Use present tense for the entry title ("Add support for..." not "Added support for...")
- Don't repeat the section heading in the entry text
- Keep bullet entries to 1-2 lines; use the sub-heading format for anything needing more explanation

---

## Phase 4: Present for Review

**CRITICAL**: This is a mandatory confirmation gate. Never skip to Phase 5 without explicit user approval.

**Present to the user**:

1. **Summary line**:
   ```
   Branch: <branch-name> | Commits: <count> | PR: #<number> (or "none")
   ```

2. **Proposed entries** in a fenced code block showing the exact markdown:
   ````
   ```markdown
   ### Bug fixes

   - Fix phantom error when processing edge case input (#512)

   #### Component: Report errors in summary output (#512)

   The handler now detects and reports failures instead of silently
   succeeding. The summary shows errored items alongside successful
   and failed counts.
   ```
   ````

3. **Insertion point**: Describe where these entries will go:
   ```
   Insert after: <identified insertion point from Phase 1>
   Before: <next section or release heading>
   ```

4. **Ask the user**: "Insert these entries into <changelog-file>? You can also ask me to modify them first."

**Wait for user response.** Do not proceed until they confirm.

---

## Phase 5: Insert into Changelog

**Goal**: Insert the approved entries into the changelog file.

**Only execute after explicit user approval in Phase 4.**

### Insertion logic

1. **Find the insertion point** identified in Phase 1

2. **Check for existing unreleased section headings**:
   - If the changelog already has a matching section heading in the unreleased block, **append** to the existing section rather than creating a duplicate heading
   - If the section doesn't exist yet, insert the full section with heading

3. **Insert the entries**:
   - Use the Edit tool to insert at the identified insertion point
   - Ensure consistent blank line spacing matching the existing file style

4. **Show the result**:
   - After editing, read the modified region of the changelog file and display it so the user can verify
   - Note: this command does NOT commit — the user decides when to stage and commit the changelog update

### Commit message conventions for CHANGES edits

When the user asks to commit the CHANGES update, follow these rules:

1. **`#PRNUM` references belong in CHANGES, never in commit messages.** CHANGES entries reference PRs (e.g., `(#511)`) because they are user-facing and link to GitHub. Commit messages must never contain `#123` — the PR number may not exist yet, and git's merge history already tracks which PR a commit belongs to.

2. **Don't be redundant with the component prefix.** The commit prefix `docs(CHANGES)` already says "this is a changelog edit." The subject line should describe *what the changelog covers*, not that a changelog was added. For example:
   - **Good**: `docs(CHANGES) Help-on-empty CLI and sync --all flag`
   - **Bad**: `docs(CHANGES) Add changelog entry for help-on-empty CLI`
   - **Bad**: `docs(CHANGES[v1.53.x]) ...` — the version is unknown until merge

3. **Use `docs(CHANGES)` as the component.** No sub-component (no `[v1.53.x]` etc.) since the target release version is not known at commit time.

### Edge case: merging with existing entries

If there are already entries in the unreleased section:

- New entries for **existing sections** are appended at the end of that section (before the next `###` heading or the next `## ` release heading)
- New entries for **new sections** follow the section order defined in Phase 3 — insert the new section in the correct position relative to existing sections
- Never duplicate a `###` section heading
