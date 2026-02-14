---
name: rebase
description: Rebase current branch onto trunk with conflict prediction, resolution, and quality gate verification. Use when asked to rebase, update from trunk, or sync with the main branch.
---

# Git Rebase

## Context

Gather the following information before proceeding:

Run `git branch --show-current` to determine the current branch.

Run `git remote show origin 2>/dev/null | grep 'HEAD branch' | awk '{print $NF}'` to determine the trunk branch.

Run `git remote -v 2>/dev/null | head -2` to see available remote refs.

Detect the trunk branch name:

```bash
TRUNK=$(git remote show origin 2>/dev/null | grep 'HEAD branch' | awk '{print $NF}')
```

If the command returned empty, try both `origin/main` and `origin/master` to see which exists.

Run the following to see commits on the current branch not on trunk:

```bash
git log --oneline "origin/${TRUNK}..HEAD" 2>/dev/null || echo "(could not determine commits ahead)"
```

Run the following to see the diff summary from trunk:

```bash
git diff --stat "origin/${TRUNK}" 2>/dev/null || echo "(could not diff against trunk)"
```

## Procedure

Rebase the current branch onto the remote trunk branch. Follow these steps carefully, handling each phase before moving to the next.

### Phase 1: Detect trunk branch

Determine the trunk branch name from the context above (the "Trunk branch" value). Store it mentally as `TRUNK`. It will typically be `master` or `main`. If detection failed, try both `origin/master` and `origin/main` to see which exists.

### Phase 2: Fetch latest and analyze

1. Run `git fetch origin` to get the latest remote state.
2. Run `git diff origin/${TRUNK}...HEAD --stat` to see what files the current branch modifies.
3. Run `git diff origin/${TRUNK}...HEAD` to see the full diff of changes on this branch.
4. Run `git log --oneline origin/${TRUNK}..HEAD` to see commits that will be rebased.
5. Run `git diff --name-only -z "origin/${TRUNK}...HEAD" | xargs -0 git diff "origin/${TRUNK}" --` to check if trunk has also modified any of the same files — these are potential conflict zones.

Report a brief summary of:
- How many commits will be rebased
- Which files were changed on this branch
- Which of those files were ALSO changed on trunk (potential conflicts)
- An assessment of conflict likelihood (none expected / minor / significant)

### Phase 3: Execute the rebase

Run:
```
git pull --rebase origin "${TRUNK}" --autostash
```

If the rebase completes cleanly (exit code 0), skip to Phase 5.

### Phase 4: Resolve conflicts (if any)

If conflicts are detected:

1. Run `git status` to see which files have conflicts.
2. For each conflicted file:
   a. Read the file to see the conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
   b. Understand both sides of the conflict by examining what the branch intended vs what trunk changed
   c. Resolve the conflict by editing the file — preserve the intent of BOTH changes when possible. When in doubt, prefer the branch's changes (the current work) but integrate trunk's changes if they're structural (renames, new parameters, etc.)
   d. Run `git add <file>` to mark it resolved
3. Before continuing the rebase, run the project's quality checks. Look for AGENTS.md / CLAUDE.md in the repo root to discover the project's required checks. Common quality gates by ecosystem:

   | Gate | Example commands |
   |------|-----------------|
   | Formatter | `ruff format`, `prettier --write`, `rustfmt`, `gofmt` |
   | Linter | `ruff check --fix`, `eslint --fix`, `clippy`, `golangci-lint` |
   | Type checker | `mypy`, `tsc --noEmit`, `basedpyright` |
   | Tests | `pytest`, `jest`, `cargo test`, `go test ./...` |

   If any check fails, fix the issues and re-stage with `git add` before continuing.
4. Run `git rebase --continue` to proceed.
5. If more conflicts appear, repeat from step 1 of this phase.
6. If the rebase becomes unrecoverable, run `git rebase --abort` and report what went wrong.

### Phase 5: Verify final state

After the rebase completes successfully:

1. Run `git log --oneline -10` to confirm the rebased commit history looks correct.
2. Run `git status` to confirm a clean working tree.
3. Run the project's quality checks one final time as described in Phase 4 step 3.
4. Report the results: how many commits were rebased, whether any conflicts were resolved, and the final state of all quality checks.

Do NOT force-push. Only report the final state and let the user decide on the next step.
