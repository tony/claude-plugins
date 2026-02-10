# multi-model

Run prompts across Claude, Gemini, and GPT in parallel — plan, execute, review, and synthesize the best of all models.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install multi-model@ai-workflow-plugins
```

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

1. **Configure** — Parse trigger words and prompt for settings if none provided.
2. **Detect models** — Check for `gemini`, `codex`, and `agent` CLIs. Use native CLIs when available, fall back to the `agent` CLI with `--model` flags.
3. **Run in parallel** — Execute the task across all available models simultaneously.
4. **Synthesize** — Compare outputs, verify claims against the codebase, and combine the best elements.
5. **Refine** (multi-pass) — Optionally re-run all models with the prior synthesis as context for deeper results.

### Read-Only Commands

**ask**, **plan**, and **review** do not modify files. They gather multiple perspectives and synthesize a single best result.

### Write Commands

**prompt** and **execute** create isolated git worktrees for each external model, so implementations never interfere with each other. After comparison:
- **prompt** picks one winner
- **execute** cherry-picks the best parts from each model

**fix-review** processes findings from a review, applying each as an atomic commit with test coverage. Multi-pass does not apply to fix-review since it is already iterative.

## Multi-Pass Refinement

Multi-pass re-runs all models with the prior synthesis prepended as context, allowing each model to challenge, deepen, or confirm the previous round's results. This produces higher-quality outputs at the cost of additional model invocations.

### Trigger Words

Append trigger words to any command's arguments to control pass count:

| Trigger | Passes | Example |
|---------|--------|---------|
| `x2` or `multipass` | 2 | `/multi-model:ask what is this project? x2` |
| `x3` or `ultrathink` | 3 | `/multi-model:plan add auth ultrathink` |
| `x<N>` (N = 2–5) | N | `/multi-model:review x4` |

Values above 5 are capped at 5.

### Timeout Triggers

Override the default timeout per command:

| Trigger | Effect | Example |
|---------|--------|---------|
| `timeout:<seconds>` | Set custom timeout | `/multi-model:ask question timeout:300` |
| `timeout:none` | Disable timeout | `/multi-model:execute task timeout:none` |

Default timeouts per command: ask (450s), plan (600s), prompt (600s), review (900s), execute (1200s).

### Interactive Configuration

When no trigger words or timeout overrides are present in the arguments, commands prompt via `AskUserQuestion` for:

1. **Pass count** — choose single pass, multipass (2), ultrathink (3), or custom (2–5)
2. **Timeout** — choose the default, quick (180s), long (900s), or no timeout

This prompt is skipped when trigger words are detected or when running in headless mode (`claude -p`), which uses defaults silently.

## Prerequisites

At minimum, Claude (this agent) is always available. For multi-model functionality, install one or more external CLIs:

| CLI | Model | Install |
|-----|-------|---------|
| `gemini` | Gemini | [Gemini CLI](https://github.com/google-gemini/gemini-cli) |
| `codex` | GPT | [Codex CLI](https://github.com/openai/codex) |
| `agent` | Any (fallback) | [Agent CLI](https://cursor.com/cli) |

### macOS timeout support

External CLI commands are wrapped with `timeout` (GNU coreutils) to enforce time
limits. On macOS, install GNU coreutils to get `gtimeout`:

```console
brew install coreutils
```

If neither `timeout` nor `gtimeout` is found, commands run without a time limit.

If no external CLIs are available, commands fall back to Claude-only mode with a note about the limitation.

## Shell Resilience

All commands use `command -v` (POSIX-portable) instead of `which` for CLI detection. Prompts are written to temporary files (`/tmp/mm-prompt-XXXXXX.txt`) to avoid shell metacharacter injection. stderr is captured to separate files (`/tmp/mm-stderr-<model>.txt`) for failure diagnostics. A structured retry protocol classifies failures (timeout, rate-limit, crash, empty output) and retries retryable failures once before marking a model unavailable.

## Language-Agnostic Design

All commands discover project-specific tooling by reading AGENTS.md / CLAUDE.md at runtime. Quality gates, test commands, and conventions are never hardcoded — they work with any language or framework.
