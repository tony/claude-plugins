# multi-model

Run prompts across Claude, Gemini, and GPT in parallel — plan, execute, review, and synthesize the best of all models.

## Commands

| Command | Description |
|---------|-------------|
| `/multi-model:ask` | Ask all models a question, synthesize the best answer |
| `/multi-model:plan` | Get implementation plans from all models, synthesize the best plan |
| `/multi-model:prompt` | Run a prompt in isolated worktrees, pick the best implementation |
| `/multi-model:execute` | Run a task in isolated worktrees, synthesize the best parts of each |
| `/multi-model:review` | Run code review with all models, produce consensus-weighted report |
| `/multi-model:fix-review` | Fix review findings as atomic commits with test coverage |

## How It Works

Each command follows a consistent multi-phase workflow:

1. **Detect models** — Check for `gemini`, `codex`, and `agent` CLIs. Use native CLIs when available, fall back to the `agent` CLI with `--model` flags.
2. **Run in parallel** — Execute the task across all available models simultaneously.
3. **Synthesize** — Compare outputs, verify claims against the codebase, and combine the best elements.

### Read-Only Commands

**ask**, **plan**, and **review** do not modify files. They gather multiple perspectives and synthesize a single best result.

### Write Commands

**prompt** and **execute** create isolated git worktrees for each external model, so implementations never interfere with each other. After comparison:
- **prompt** picks one winner
- **execute** cherry-picks the best parts from each model

**fix-review** processes findings from a review, applying each as an atomic commit with test coverage.

## Prerequisites

At minimum, Claude (this agent) is always available. For multi-model functionality, install one or more external CLIs:

| CLI | Model | Install |
|-----|-------|---------|
| `gemini` | Gemini | [Gemini CLI](https://github.com/google-gemini/gemini-cli) |
| `codex` | GPT | [Codex CLI](https://github.com/openai/codex) |
| `agent` | Any (fallback) | [Agent CLI](https://github.com/anthropics/agent) |

If no external CLIs are available, commands fall back to Claude-only mode with a note about the limitation.

## Language-Agnostic Design

All commands discover project-specific tooling by reading AGENTS.md / CLAUDE.md at runtime. Quality gates, test commands, and conventions are never hardcoded — they work with any language or framework.
