# changelog

Generate categorized changelog entries from branch commits and PR context.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install changelog@ai-workflow-plugins
```

## Command

| Command | Description |
|---------|-------------|
| `/changelog` | Analyze commits, categorize changes, and insert entries into the changelog |

## 5-Phase Workflow

1. **Gather context** — Detect project name, find changelog file, analyze its format, check for PR, collect commits
2. **Categorize commits** — Parse commit types, group related commits (e.g., TDD sequences collapse into one entry)
3. **Generate entries** — Write markdown matching the existing changelog style
4. **Present for review** — Show proposed entries and insertion point, wait for user approval
5. **Insert** — Apply approved entries to the changelog file

## Supported Changelog Formats

The command auto-detects the changelog format from the existing file:

| File names | `CHANGES`, `CHANGES.md`, `CHANGELOG`, `CHANGELOG.md`, `HISTORY.md`, `NEWS.md` |
|------------|--------------------------------------------------------------------------------|
| Heading styles | `## v1.2.3`, `## [1.2.3]`, `## project v1.2.3`, `## 1.2.3 (YYYY-MM-DD)` |
| Insertion points | Placeholder comments, `## [Unreleased]` headings, top of file |

## Commit Categorization

Commits are mapped to changelog sections based on their type prefix:

| Commit type | Section |
|-------------|---------|
| `feat` | Features |
| `fix` | Bug fixes |
| `docs` | Documentation |
| `test` | Tests |
| `chore`, `deps` | Development |

Related commits are grouped automatically:
- TDD sequences (xfail → fix → remove xfail) collapse into a single bug fix entry
- Sequential feature commits on the same component merge into one entry
- Merge commits and formatting-only changes are skipped

## Prerequisites

- **git** — for commit history analysis
- **gh** (optional) — for PR number and label detection

## Language-Agnostic Design

Project name detection works across ecosystems: `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, or the repository directory name. The changelog format is detected from the existing file — no format is assumed.
