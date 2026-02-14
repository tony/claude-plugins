---
name: commit
description: Create git commits following project conventions with format enforcement and safety checks. Use when asked to commit changes, stage and commit, or create a commit message.
---

# Git Commit

Create a well-formatted git commit using the project's commit conventions.

## Context

Gather the following context before proceeding:

Run `git branch --show-current` to determine the current branch.

Run `git status --short` to see working tree status.

Run `git diff --cached --stat` to see staged changes.

Run `git diff --stat` to see unstaged changes.

Run `git diff HEAD` to see the full diff against HEAD.

Run `git log --oneline -10` to see recent commits for style matching.

---

## Commit Convention

Read the project's AGENTS.md / CLAUDE.md to discover the commit message format. Look for:
- Subject line format (e.g., `Scope(type[detail]) description`, Conventional Commits `type(scope): description`, or other patterns)
- Body structure (e.g., `why:/what:` sections)
- Component naming conventions

If no project convention is found, fall back to Conventional Commits: `type(scope): description`.

Match the style of the recent commits shown above — capitalization, tense, level of detail.

---

## Procedure

### 1. Analyze Changes

- Review the full diff to understand what changed
- Determine the commit type (`feat`, `fix`, `refactor`, `docs`, `chore`, `test`, `style`, etc.)
- Determine the scope/component from the files and modules touched
- Check topic coherence: if the changes span unrelated topics, warn the user and suggest splitting into separate commits

### 2. Determine Staging

- **If files are already staged** (`git diff --cached` is non-empty): respect the user's staging — only commit what is staged
- **If nothing is staged**: auto-stage changed files, but:
  - **Never stage sensitive files**: `.env`, `.env.*`, `*.pem`, `*.key`, `*credentials*`, `*secret*`, `*.p12`, `*.pfx`, `id_rsa*`, `*.keystore`
  - Use `git add <specific-files>` — never `git add -A` or `git add .`
  - Tell the user which files are being staged

### 3. Draft Commit Message

- Follow the project's commit format discovered above
- If the user provided a hint in the conversation, use it for the description — but always enforce the project's format
- Include a body (`why:/what:` or equivalent) when:
  - Multiple files are changed
  - The change is non-trivial
  - The diff is not self-explanatory
- **Show the proposed commit message** to the user before executing

### 4. Commit

- For single-line messages:
  ```
  git commit -m "the message"
  ```
- For messages with a body, use heredoc to preserve formatting:
  ```
  git commit -m "$(cat <<'EOF'
  subject line

  why: ...
  what:
  - ...
  EOF
  )"
  ```
- **If a pre-commit hook fails**:
  - Read the hook output to understand the failure
  - Fix the issue (formatting, lint, etc.)
  - Re-stage the fixed files
  - Create a **new** commit — never use `--amend` (the failed commit does not exist)

### 5. Confirm Result

Run `git log --oneline -1` to show the created commit.

Run `git status` to show the remaining working tree state.

Report success to the user.

---

## Rules

- **Never** run `git push`, `git push --force`, `git reset --hard`, or any destructive git command
- **Never** use `--amend` — always create new commits
- **Never** use `--no-verify` or `--no-gpg-sign`
- **Never** create empty commits
- **Never** use `git add -A` or `git add .`
- **Never** commit files that likely contain secrets (`.env`, credentials, keys)
- Always use heredoc when the commit message has a body (multi-line)
- Always present the proposed commit message before executing `git commit`
- If there are no changes to commit, report "Nothing to commit" and stop
