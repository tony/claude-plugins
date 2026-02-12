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

Append trigger words to any command's arguments to hint at pass count:

| Trigger | Effect | Example |
|---------|--------|---------|
| `multipass` | Hints 2 passes | `/multi-model:ask what is this? multipass` |
| `x<N>` (N = 2–5) | Hints N passes | `/multi-model:plan add auth x3` |

Triggers are hints — commands always prompt for confirmation. Values above 5 are capped at 5. Only the first and last line of arguments are scanned; trigger-like words found elsewhere prompt for disambiguation.

### Timeout Triggers

Override the default timeout per command:

| Trigger | Effect | Example |
|---------|--------|---------|
| `timeout:<seconds>` | Set custom timeout | `/multi-model:ask question timeout:300` |
| `timeout:none` | Disable timeout | `/multi-model:execute task timeout:none` |

Default timeouts per command: ask (450s), plan (600s), prompt (600s), review (900s), execute (1200s).

### Interactive Configuration

Commands always prompt via `AskUserQuestion` for pass count, with trigger hints biasing the recommended option:

1. **Pass count** (always asked) — choose single pass (1), multipass (2), or triple pass (3). If a trigger hint is present, the matching option is marked as recommended.
2. **Timeout** (asked unless structured trigger present) — choose the default, quick (180s), long (900s), or no timeout. Skipped when `timeout:<seconds>` or `timeout:none` is provided.

In headless mode (`claude -p`), pass count uses the trigger hint value if present, otherwise defaults to 1. Timeout uses the parsed value if provided, otherwise the per-command default.

## Session Artifacts

All commands persist model outputs, prompts, and synthesis results to a structured directory under `$AI_AIP_ROOT`. This enables post-session inspection, selective reference to prior pass artifacts during multi-pass refinement, and lightweight resume tracking.

### Storage Root Resolution

The storage root is resolved in this order:

1. `$AI_AIP_ROOT` environment variable (if set)
2. `$XDG_STATE_HOME/ai-aip` (if `$XDG_STATE_HOME` is set)
3. `$HOME/.local/state/ai-aip` (Linux default)
4. `~/Library/Application Support/ai-aip` (macOS, when neither `$AI_AIP_ROOT` nor `$XDG_STATE_HOME` is set)
5. `~/.ai-aip` (final fallback)

A `/tmp/ai-aip` symlink is created pointing to the resolved root for backward compatibility.

### Repo Identity

Repos are identified by a combination of a slugified directory name and a 12-character SHA-256 hash of the repo key (origin URL + slug, or absolute path for repos without a remote). This prevents collisions between unrelated repos with the same directory name.

Format: `<slug>--<hash>` (e.g., `my-project--a1b2c3d4e5f6`)

### Session Identity

Session IDs combine a UTC timestamp, PID, and random bytes to prevent collisions:

```
<YYYYMMDD-HHMMSSz>-<PID>-<4 hex chars>
```

Example: `20260210-143022Z-12345-a1b2`

### Directory Hierarchy

```
$AI_AIP_ROOT/
└── repos/
    └── <slug>--<hash>/
        ├── repo.json
        └── sessions/
            ├── ask/
            │   ├── latest -> <SESSION_ID>
            │   └── <SESSION_ID>/
            │       ├── session.json
            │       ├── events.jsonl
            │       ├── metadata.md
            │       ├── pass-0001/
            │       │   ├── prompt.md
            │       │   ├── synthesis.md
            │       │   ├── outputs/
            │       │   │   ├── claude.md
            │       │   │   ├── gemini.md
            │       │   │   └── gpt.md
            │       │   └── stderr/
            │       │       ├── gemini.txt
            │       │       └── gpt.txt
            │       └── pass-0002/
            │           └── ...
            ├── plan/
            │   └── ...
            ├── review/
            │   └── ...
            ├── execute/
            │   └── ...
            └── prompt/
                └── ...
```

Write commands (execute, prompt) add per-pass diff and quality gate artifacts:

```
pass-0001/
├── ...
├── quality-gates.md
└── diffs/
    ├── claude.diff
    ├── gemini.diff
    └── gpt.diff
```

Pass directories use zero-padded 4-digit numbering (`pass-0001`, `pass-0002`, ...) for correct lexicographic sorting. Directories are created with `mkdir -p -m 700` and are preserved after the session for user inspection.

### Repo Manifest (`repo.json`)

Each `repos/<slug>--<hash>/` directory contains a `repo.json` written on the first session for that repo:

```json
{
  "schema_version": 1,
  "slug": "my-project",
  "id": "a1b2c3d4e5f6",
  "toplevel": "/home/user/projects/my-project",
  "origin": "git@github.com:user/my-project.git"
}
```

### Session Manifest (`session.json`)

Each session directory contains a `session.json` that tracks session state. Updated via atomic replace (write to `.tmp`, then `mv`):

```json
{
  "schema_version": 1,
  "session_id": "20260210-143022Z-12345-a1b2",
  "command": "ask",
  "status": "in_progress",
  "branch": "feature/add-auth",
  "ref": "abc1234",
  "models": ["claude", "gemini", "gpt"],
  "completed_passes": 0,
  "prompt_summary": "How does the authentication middleware work?",
  "created_at": "2026-02-10T14:30:22Z",
  "updated_at": "2026-02-10T14:30:22Z"
}
```

| Field | Description |
|-------|-------------|
| `schema_version` | Always `1` |
| `session_id` | Session directory name |
| `command` | Which command created this session |
| `status` | `in_progress` or `completed` |
| `branch` | Git branch at session start |
| `ref` | Git commit ref (short SHA) at session start |
| `models` | Which models participated |
| `completed_passes` | How many passes finished |
| `prompt_summary` | First 120 chars of the user's prompt |
| `created_at` | ISO 8601 UTC timestamp of session start |
| `updated_at` | ISO 8601 UTC timestamp of last update |

The session is updated after each pass (`completed_passes` incremented, `updated_at` refreshed) and at session end (`status` set to `completed`). A `latest` symlink is updated at session end to point to the most recent completed session.

### Event Log (`events.jsonl`)

Each session directory contains an `events.jsonl` file with one JSON object per line:

```json
{"event":"session_start","timestamp":"2026-02-10T14:30:22Z","command":"ask","models":["claude","gemini","gpt"]}
```

```json
{"event":"pass_complete","timestamp":"2026-02-10T14:32:45Z","pass":1,"models_completed":["claude","gemini","gpt"]}
```

```json
{"event":"session_complete","timestamp":"2026-02-10T14:32:50Z","completed_passes":1}
```

To list sessions, scan `session.json` files under `$AI_AIP_ROOT/repos/<slug>--<hash>/sessions/<command>/`. The `latest` symlink points to the most recently completed session for quick access.

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

All commands use `command -v` (POSIX-portable) instead of `which` for CLI detection. Prompts are written to the session directory (`$SESSION_DIR/pass-NNNN/prompt.md`) to avoid shell metacharacter injection while also persisting artifacts. stderr is captured per-pass (`$SESSION_DIR/pass-NNNN/stderr/<model>.txt`) for failure diagnostics. A structured retry protocol classifies failures (timeout, rate-limit, crash, empty output) and retries retryable failures once before marking a model unavailable.

## Language-Agnostic Design

All commands discover project-specific tooling by reading AGENTS.md / CLAUDE.md at runtime. Quality gates, test commands, and conventions are never hardcoded — they work with any language or framework.
