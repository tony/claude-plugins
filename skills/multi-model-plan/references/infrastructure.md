# Multi-Model Shared Infrastructure

This document describes the shared configuration, session management, execution strategy, and completion protocol for the multi-model plan skill.

---

## Phase 2: Configuration and Model Detection

### Step 1: Parse Trigger Words

Only the **first line and last line** of the user's request are scanned for triggers (case-insensitively). This prevents pasted content in the body from accidentally matching. If a trigger-like word appears elsewhere but not on the first/last line, ask the user whether they intended it as a trigger. Strip matched triggers from the prompt text before sending to models.

**Multi-pass triggers**:

| Trigger | Effect |
|---------|--------|
| `multipass` (case-insensitive) | Hint for 2 passes |
| `x<N>` (N = 2–5, regex `\bx([2-5])\b`) | Hint for N passes |

Values above 5 are capped at 5 with a note to the user.

**Timeout triggers**:

| Trigger | Effect |
|---------|--------|
| `timeout:<seconds>` | Override default timeout |
| `timeout:none` | Disable timeout |

**Config flags** (used in Step 2):
- `pass_hint` = parsed pass count if trigger found on first/last line, else null. If trigger found only in body, ask user to disambiguate before setting.
- `has_timeout_config` = true if `timeout:<seconds>` or `timeout:none` found on first/last line. If found only in body, ask user to disambiguate before setting.

### Step 2: Interactive Configuration

**Question 1 (Passes) — always asked**. Trigger hints only change option ordering.

If running in headless/non-interactive mode, use `pass_hint` value if set, otherwise default to 1 pass. Timeout uses parsed value if `has_timeout_config`, otherwise 600s.

Ask the user:

**Question 1 — Passes** (always asked):
- question: "How many synthesis passes? Multi-pass re-runs all models with prior results for deeper refinement."
- When `pass_hint` exists (trigger found), move the matching option first with "(Recommended)" suffix. Other options follow in ascending order.
- When `pass_hint` is null (no trigger), use default ordering:
  - "1 — single pass (Recommended)" — Run models once and synthesize. Sufficient for most tasks.
  - "2 — multipass" — One refinement round. Models see prior synthesis and can challenge or deepen it.
  - "3 — triple pass" — Two refinement rounds. Maximum depth, highest token usage.

**Question 2 — Timeout** (skipped only when `has_timeout_config` is true):
- question: "Timeout for external model commands?"
- options:
  - "Default (600s)" — Use this skill's built-in default timeout.
  - "Quick — 3 min (180s)" — For fast queries. May timeout on complex tasks.
  - "Long — 15 min (900s)" — For complex planning tasks. Higher wait on failures.
  - "None" — No timeout. Wait indefinitely for each model.

### Step 3: Detect Available Models

**Goal**: Check which AI CLI tools are installed locally.

Run these checks in parallel:

```bash
command -v gemini >/dev/null 2>&1 && echo "gemini:available" || echo "gemini:missing"
```

```bash
command -v codex >/dev/null 2>&1 && echo "codex:available" || echo "codex:missing"
```

```bash
command -v agent >/dev/null 2>&1 && echo "agent:available" || echo "agent:missing"
```

#### Model resolution (priority order)

| Slot | Priority 1 (native) | Priority 2 (agent fallback) | Agent model |
|------|---------------------|-----------------------------|-------------|
| **Claude** | Always available (the current agent) | — | — |
| **Gemini** | `gemini` binary | `agent --model gemini-3-pro` | `gemini-3-pro` |
| **GPT** | `codex` binary | `agent --model gpt-5.2` | `gpt-5.2` |

**Resolution logic** for each external slot:
1. Native CLI found → use it
2. Else `agent` found → use `agent` with `--model` flag
3. Else → slot unavailable, note in report

Report which models will participate and which backend each uses.

### Step 4: Detect Timeout Command

```bash
command -v timeout >/dev/null 2>&1 && echo "timeout:available" || { command -v gtimeout >/dev/null 2>&1 && echo "gtimeout:available" || echo "timeout:none"; }
```

On Linux, `timeout` is available by default. On macOS, `gtimeout` is available via GNU coreutils. If neither is found, run external commands without a timeout prefix — time limits will not be enforced. Do not install packages automatically.

Store the resolved timeout command (`timeout`, `gtimeout`, or empty) for use in all subsequent CLI invocations. When constructing bash commands, replace `<timeout_cmd>` with the resolved command and `<timeout_seconds>` with the resolved value (from trigger parsing, interactive config, or the default of 600). If no timeout command is available, omit the prefix entirely.

---

## Phase 2b: Initialize Session Directory

**Goal**: Create a persistent session directory for all artifacts across passes.

### Step 1: Resolve storage root

```bash
if [ -n "$AI_AIP_ROOT" ]; then
  AIP_ROOT="$AI_AIP_ROOT"
elif [ -n "$XDG_STATE_HOME" ]; then
  AIP_ROOT="$XDG_STATE_HOME/ai-aip"
elif [ "$(uname -s)" = "Darwin" ]; then
  AIP_ROOT="$HOME/Library/Application Support/ai-aip"
else
  AIP_ROOT="$HOME/.local/state/ai-aip"
fi
```

Create a `/tmp/ai-aip` symlink to the resolved root for backward compatibility (if `/tmp/ai-aip` doesn't already exist or isn't already correct):

```bash
ln -sfn "$AIP_ROOT" /tmp/ai-aip 2>/dev/null || true
```

### Step 2: Compute repo identity

```bash
REPO_TOPLEVEL="$(git rev-parse --show-toplevel)"
```

```bash
REPO_SLUG="$(basename "$REPO_TOPLEVEL" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9._-]/-/g')"
```

```bash
REPO_ORIGIN="$(git remote get-url origin 2>/dev/null || true)"
```

```bash
if [ -n "$REPO_ORIGIN" ]; then
  REPO_KEY="${REPO_ORIGIN}|${REPO_SLUG}"
else
  REPO_KEY="$REPO_TOPLEVEL"
fi
```

```bash
if command -v sha256sum >/dev/null 2>&1; then
  REPO_ID="$(printf '%s' "$REPO_KEY" | sha256sum | cut -c1-12)"
else
  REPO_ID="$(printf '%s' "$REPO_KEY" | shasum -a 256 | cut -c1-12)"
fi
```

```bash
REPO_DIR="${REPO_SLUG}--${REPO_ID}"
```

### Step 3: Generate session ID

```bash
SESSION_ID="$(date -u '+%Y%m%d-%H%M%SZ')-$$-$(head -c2 /dev/urandom | od -An -tx1 | tr -d ' ')"
```

### Step 4: Create session directory

```bash
SESSION_DIR="$AIP_ROOT/repos/$REPO_DIR/sessions/plan/$SESSION_ID"
mkdir -p -m 700 "$SESSION_DIR/pass-0001/outputs" "$SESSION_DIR/pass-0001/stderr"
```

### Step 5: Write `repo.json` (if missing)

If `$AIP_ROOT/repos/$REPO_DIR/repo.json` does not exist, write it with these contents:

```json
{
  "schema_version": 1,
  "slug": "<REPO_SLUG>",
  "id": "<REPO_ID>",
  "toplevel": "<REPO_TOPLEVEL>",
  "origin": "<REPO_ORIGIN or null>"
}
```

### Step 6: Write `session.json` (atomic replace)

Write to `$SESSION_DIR/session.json.tmp`, then `mv session.json.tmp session.json`:

```json
{
  "schema_version": 1,
  "session_id": "<SESSION_ID>",
  "command": "plan",
  "status": "in_progress",
  "branch": "<current branch>",
  "ref": "<short SHA>",
  "models": ["claude", "..."],
  "completed_passes": 0,
  "prompt_summary": "<first 120 chars of task description>",
  "created_at": "<ISO 8601 UTC>",
  "updated_at": "<ISO 8601 UTC>"
}
```

### Step 7: Append `events.jsonl`

Append one event line to `$SESSION_DIR/events.jsonl`:

```json
{"event":"session_start","timestamp":"<ISO 8601 UTC>","command":"plan","models":["claude","..."]}
```

### Step 8: Write `metadata.md`

Write to `$SESSION_DIR/metadata.md` containing:
- Command: `plan`, start time, configured pass count
- Models detected, timeout setting
- Git branch (run `git branch --show-current`), commit ref (run `git rev-parse --short HEAD`)

Store `$SESSION_DIR` for use in all subsequent phases.

---

## Execution Strategy

For each external CLI invocation:
1. **Record**: exit code, stderr (from `$SESSION_DIR/pass-{N}/stderr/<model>.txt`), elapsed time
2. **Classify failure**: timeout → retryable with 1.5× timeout; API/rate-limit error → retryable after 10s delay; crash → not retryable; empty output → retryable once
3. **Retry**: max 1 retry per model per pass
4. **After retry failure**: mark model as unavailable for this pass, include failure details in report
5. **Continue**: never block entire workflow on single model failure

---

## Session Completion Protocol

At session end:
1. Update `session.json` via atomic replace: set `status` to `"completed"`, `updated_at` to now
2. Append a `session_complete` event to `events.jsonl`
3. Update `latest` symlink:
   ```bash
   ln -sfn "$SESSION_ID" "$AIP_ROOT/repos/$REPO_DIR/sessions/plan/latest"
   ```
4. Include `**Session artifacts**: $SESSION_DIR` in the final output
