# ai-workflow-plugins

An [OpenSkills](https://openskills.dev) repository providing language-agnostic AI workflow
skills for developer experience efficiency.

**Repository:** [tony/ai-workflow-plugins](https://github.com/tony/ai-workflow-plugins)

## Skills

| Skill | Category | Description |
|-------|----------|-------------|
| [commit](skills/commit/) | Development | Create git commits following project conventions with format enforcement and safety checks |
| [changelog](skills/changelog/) | Productivity | Generate categorized changelog entries from branch commits and PR context |
| [rebase](skills/rebase/) | Development | Rebase onto trunk with conflict prediction, resolution, and quality gate verification |
| [tdd-fix](skills/tdd-fix/) | Testing | TDD bug-fix workflow — reproduce bugs as failing tests, find root cause, fix, and verify |
| [codex-cli](skills/codex-cli/) | Development | Delegate a task to OpenAI GPT via the Codex CLI with automatic fallback |
| [gemini-cli](skills/gemini-cli/) | Development | Delegate a task to Google Gemini via the gemini CLI with automatic fallback |
| [cursor-cli](skills/cursor-cli/) | Development | Delegate a task to Cursor's agent CLI |
| [gpt-cli](skills/gpt-cli/) | Development | Alias for codex-cli |
| [multi-model-ask](skills/multi-model-ask/) | Development | Ask all models a question in parallel, synthesize the best answer |
| [multi-model-plan](skills/multi-model-plan/) | Development | Get plans from all models, synthesize the best plan |
| [multi-model-prompt](skills/multi-model-prompt/) | Development | Run a prompt in isolated worktrees per model, pick the best implementation |
| [multi-model-execute](skills/multi-model-execute/) | Development | Run a task in isolated worktrees per model, synthesize the best parts |
| [multi-model-architecture](skills/multi-model-architecture/) | Development | Generate project scaffolding from all models, synthesize the best architecture |
| [multi-model-review](skills/multi-model-review/) | Development | Run code review with all models, produce a consensus-weighted report |
| [multi-model-fix-review](skills/multi-model-fix-review/) | Development | Fix multi-model review findings as atomic commits with test coverage |

## Installation

```console
npx openskills install tony/ai-workflow-plugins
```

## Prerequisites

- **git** — required for all version control skills (commit, changelog, rebase, tdd-fix)
- **gh** — GitHub CLI, used by changelog for PR context

For multi-model and CLI delegation skills, install one or more external AI CLIs:

| CLI | Model | Install |
|-----|-------|---------|
| `gemini` | Google Gemini | [Gemini CLI](https://github.com/google-gemini/gemini-cli) |
| `codex` | OpenAI GPT | [Codex CLI](https://github.com/openai/codex) |
| `agent` | Cursor (also fallback for gemini/codex) | Cursor CLI |

Skills detect available CLIs at runtime and report which models will participate.

## Design Philosophy

Every skill in this repository is **language-agnostic**. Skills do not hardcode
language-specific tools like `pytest`, `jest`, `cargo test`, or `ruff`. Instead, they
reference the project's own conventions by reading `AGENTS.md` or `CLAUDE.md` at
runtime to discover:

- How to run the test suite
- How to run linters and formatters
- How to run type checkers
- What commit message format to use
- What test patterns to follow

This means the same skill works whether the project uses Python, TypeScript, Rust, Go,
or any other language.

## License

MIT
