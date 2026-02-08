# commit

Create git commits following project conventions with format enforcement and safety checks.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install commit@ai-workflow-plugins
```

## Command

| Command | Description |
|---------|-------------|
| `/commit` | Analyze changes, draft a conventional commit message, and commit |

## How It Works

1. **Analyze changes** — review the diff, determine commit type and scope, check topic coherence
2. **Determine staging** — respect existing staged files; auto-stage only if nothing is staged; exclude secrets
3. **Draft commit message** — read AGENTS.md/CLAUDE.md for the project's format; match recent commit style
4. **Commit** — present the message, then execute; handle pre-commit hook failures by fixing and retrying
5. **Confirm result** — show the created commit and remaining working tree state

## Arguments

Pass an optional hint to influence the commit description:

```
/commit fix the auth bug
/commit add retry logic to the API client
```

The hint supplements auto-detection — the project's commit format is always enforced.

## Commit Format Detection

The command reads AGENTS.md and CLAUDE.md to discover the project's commit convention. It also inspects the last 10 commits for style matching. If no convention is found, it falls back to Conventional Commits (`type(scope): description`).

## Safety

- Never runs `git push`, `git reset --hard`, or other destructive commands
- Never uses `--amend` — always creates new commits
- Never stages `.env`, credentials, or key files
- Never uses `git add -A` or `git add .` — stages specific files only
- Uses heredoc formatting for multi-line commit messages

## Prerequisites

- **git** — for all version control operations
