# model-cli

Run prompts through individual AI CLIs — codex/GPT, gemini, and cursor/agent with fallback support.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install model-cli@ai-workflow-plugins
```

## Commands

| Command | Description |
|---------|-------------|
| `/model-cli:codex` | Run a prompt through the Codex CLI (OpenAI GPT), fall back to agent |
| `/model-cli:gpt` | Alias for codex — same backend, same fallback |
| `/model-cli:gemini` | Run a prompt through the Gemini CLI, fall back to agent |
| `/model-cli:cursor` | Run a prompt through Cursor's agent CLI directly |

## Skills

| Skill | Triggered when |
|-------|---------------|
| Codex CLI | User asks to use Codex, GPT, or OpenAI for a task |
| Gemini CLI | User asks to use Gemini or Google's model for a task |
| Cursor Agent CLI | User asks to use Cursor or the agent CLI for a task |

Skills are model-invoked — Claude uses them automatically when it determines delegation to another model is appropriate.

## How It Works

Each command follows a 4-phase workflow:

1. **Capture** — Parse `$ARGUMENTS` as the prompt. Extract `timeout:<seconds>` or `timeout:none` triggers.
2. **Detect** — Check for the native CLI binary, then the `agent` fallback. Detect `timeout`/`gtimeout` for time limits.
3. **Execute** — Write prompt to a temp file, run the CLI with timeout and stderr capture, retry on transient failures.
4. **Return** — Present the output, report which backend was used, clean up temp files.

### Fallback Resolution

| Command | Primary CLI | Fallback | Agent model |
|---------|------------|----------|-------------|
| `codex` / `gpt` | `codex` | `agent --model gpt-5.2` | `gpt-5.2` |
| `gemini` | `gemini` | `agent --model gemini-3-pro` | `gemini-3-pro` |
| `cursor` | `agent` | none | — |

### Timeout

Default timeout is 600 seconds. Override with `timeout:<seconds>` or disable with `timeout:none` in the command arguments.

## Prerequisites

Install at least one external CLI:

| CLI | Model | Install |
|-----|-------|---------|
| `codex` | GPT | [Codex CLI](https://github.com/openai/codex) |
| `gemini` | Gemini | [Gemini CLI](https://github.com/google-gemini/gemini-cli) |
| `agent` | Cursor (also used as fallback) | [Agent CLI](https://cursor.com/cli) |

### macOS timeout support

External CLI commands are wrapped with `timeout` (GNU coreutils) to enforce time limits. On macOS, install GNU coreutils to get `gtimeout`:

```console
brew install coreutils
```

If neither `timeout` nor `gtimeout` is found, commands run without a time limit.

## Comparison with multi-model

The **multi-model** plugin runs all models in parallel and synthesizes results. The **model-cli** plugin runs a single model at a time — useful when you want to target a specific model without the overhead of parallel orchestration.

| Feature | multi-model | model-cli |
|---------|-------------|-----------|
| Parallel execution | All models at once | Single model |
| Synthesis | Best-of-all merge | Direct output |
| Multi-pass refinement | Supported | Not applicable |
| Worktree isolation | For write commands | Not needed |

## Shell Resilience

All commands use `command -v` (POSIX-portable) instead of `which` for CLI detection. Prompts are written to temporary files (`/tmp/mc-prompt-XXXXXX.txt`) to avoid shell metacharacter injection. stderr is captured to separate files (`/tmp/mc-stderr-<model>.txt`) for failure diagnostics. A retry protocol classifies failures (timeout, rate-limit, crash, empty output) and retries transient failures once before reporting.
