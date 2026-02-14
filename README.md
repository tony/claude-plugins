# ai-workflow-plugins

A Vercel Skills repository providing language-agnostic AI workflow skills for 40+ coding agents.

**Repository:** [tony/ai-workflow-plugins](https://github.com/tony/ai-workflow-plugins)

## Skills

### Curated (stable, standalone workflows)

| Skill | Directory | Description |
|-------|-----------|-------------|
| commit | `.curated/commit` | Create git commits following project conventions with format enforcement and safety checks |
| changelog | `.curated/changelog` | Generate categorized changelog entries from branch commits and PR context |
| rebase | `.curated/rebase` | Rebase onto trunk with conflict prediction, resolution, and quality gate verification |
| tdd-fix | `.curated/tdd-fix` | TDD bug-fix workflow — reproduce bugs as failing tests, find root cause, fix, and verify |

### Experimental (advanced, external tool dependencies)

#### Multi-Model Collaboration

| Skill | Directory | Description |
|-------|-----------|-------------|
| multi-model-ask | `.experimental/multi-model-ask` | Ask all models a question in parallel, synthesize best answer |
| multi-model-plan | `.experimental/multi-model-plan` | Get implementation plans from all models, synthesize best plan |
| multi-model-prompt | `.experimental/multi-model-prompt` | Run a prompt in isolated worktrees per model, pick the best |
| multi-model-execute | `.experimental/multi-model-execute` | Synthesize the best parts from all model implementations |
| multi-model-architecture | `.experimental/multi-model-architecture` | Generate project scaffolding from all models, synthesize best architecture |
| multi-model-review | `.experimental/multi-model-review` | Consensus-weighted multi-model code review |
| multi-model-fix-review | `.experimental/multi-model-fix-review` | Fix review findings as atomic commits with test coverage |

#### CLI Delegation

| Skill | Directory | Description |
|-------|-----------|-------------|
| codex-cli | `.experimental/codex-cli` | Delegate to OpenAI GPT via Codex CLI with automatic fallback |
| gemini-cli | `.experimental/gemini-cli` | Delegate to Google Gemini CLI with automatic fallback |
| cursor-cli | `.experimental/cursor-cli` | Delegate to Cursor's agent CLI directly |
| gpt-cli | `.experimental/gpt-cli` | Alias for codex-cli |

## Installation

Install all skills:

```bash
npx skills add tony/ai-workflow-plugins
```

Install a specific skill:

```bash
npx skills add tony/ai-workflow-plugins --skill commit -a claude-code -y
```

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

This means the same skill works whether your project uses Python, TypeScript, Rust, Go,
or any other language.

## License

MIT
