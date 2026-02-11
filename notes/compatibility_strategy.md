# Cross-Platform SKILL.md Compatibility Strategy

Research into cross-platform AI CLI skill compatibility (February 2026).

## CLIs Tested

| CLI | Version / Commit | Source |
|-----|-----------------|--------|
| [Claude Code](https://code.claude.com/) | Production (Feb 2026) | Anthropic |
| [Codex CLI](https://github.com/openai/codex) | `8b7f8af34` | OpenAI |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | `0.30.0-nightly.20260210` (`63e9d5d15`) | Google |
| [Cursor](https://cursor.com/) | Production (Feb 2026) | Anysphere |

## SKILL.md Format Compatibility

All four CLIs use the same file format: YAML frontmatter + markdown body in a file
named `SKILL.md`.

### Required Frontmatter Fields

| Field | Claude Code | Codex CLI | Gemini CLI | Cursor |
|-------|:-----------:|:---------:|:----------:|:------:|
| `name` | yes | yes | yes | yes |
| `description` | yes | yes | yes | yes |

### Claude Code Extended Fields

Claude Code supports additional frontmatter fields that the other CLIs do not use:

- `user-invocable` (boolean)
- `allowed-tools` (list)
- `argument-hint` (string)
- `disable-model-invocation` (boolean)
- `version`, `tools`, `disallowedTools`, `context`

### Unknown Field Handling

All four CLIs silently ignore unknown frontmatter fields:

**Codex CLI** — Uses Rust Serde deserialization without `#[serde(deny_unknown_fields)]`.
The `SkillFrontmatter` struct extracts only `name`, `description`, and `metadata`.
Any other fields are discarded during parsing.

Source: [`codex-rs/core/src/skills/loader.rs:31-43`](https://github.com/openai/codex/blob/8b7f8af34/codex-rs/core/src/skills/loader.rs#L31-L43)

```rust
#[derive(Debug, Deserialize)]
struct SkillFrontmatter {
    name: String,
    description: String,
    #[serde(default)]
    metadata: SkillFrontmatterMetadata,
}
```

**Gemini CLI** — Uses JavaScript destructuring to extract only `name` and `description`
from the parsed YAML object. Remaining fields are never referenced.

Source: [`packages/core/src/skills/skillLoader.ts:39-59`](https://github.com/google-gemini/gemini-cli/blob/63e9d5d15/packages/core/src/skills/skillLoader.ts#L39-L59)

```typescript
const { name, description } = parsed as Record<string, unknown>;
```

**Claude Code** — Parses its own extended frontmatter schema; fields it defines are
consumed, fields from other tools would be unknown and ignored by the same principle.

**Cursor** — Scans `.claude/skills/` and `.codex/skills/` directories natively (per
[Cursor Skills docs](https://cursor.com/docs/context/skills.md), accessed Feb 2026).
Uses the same `name`/`description` extraction pattern.

### Conclusion

A single SKILL.md with Claude Code's superset frontmatter works in all four CLIs
without modification.

## Skill Discovery Paths

### Project-Level (Repo) Discovery

| Path | Claude Code | Codex CLI | Gemini CLI | Cursor |
|------|:-----------:|:---------:|:----------:|:------:|
| `.claude/skills/` | yes | — | — | yes |
| `.codex/skills/` | — | yes | — | yes |
| `.gemini/skills/` | — | — | yes | — |
| `.agents/skills/` | — | yes | yes | — |

### User-Level Discovery

| Path | Claude Code | Codex CLI | Gemini CLI |
|------|:-----------:|:---------:|:----------:|
| `~/.claude/skills/` | yes | — | — |
| `$CODEX_HOME/skills/` | — | yes | — |
| `~/.gemini/skills/` | — | — | yes |
| `~/.agents/skills/` | — | yes | yes |

### Source References

**Codex CLI** discovery paths:

- Project: `.codex/skills/` (config layer `Project`)
- Repo agents: `.agents/skills/` (walked from project root to cwd)
- User: `$CODEX_HOME/skills/`, `~/.agents/skills/`
- Admin: `/etc/codex/skills/`
- Follows symlinks for Repo, User, and Admin scopes

Source: [`codex-rs/core/src/skills/loader.rs:177-280`](https://github.com/openai/codex/blob/8b7f8af34/codex-rs/core/src/skills/loader.rs#L177-L280)

**Gemini CLI** discovery paths (precedence order, lowest to highest):

1. Built-in skills
2. Extension skills
3. User skills: `~/.gemini/skills/`
4. User agent skills: `~/.agents/skills/`
5. Workspace skills: `.gemini/skills/`
6. Workspace agent skills: `.agents/skills/`

Source: [`packages/core/src/skills/skillManager.ts:47-92`](https://github.com/google-gemini/gemini-cli/blob/63e9d5d15/packages/core/src/skills/skillManager.ts#L47-L92)

Glob pattern: `SKILL.md` or `*/SKILL.md` (one level deep).

Source: [`packages/core/src/skills/skillLoader.ts:125`](https://github.com/google-gemini/gemini-cli/blob/63e9d5d15/packages/core/src/skills/skillLoader.ts#L125)

## Command Format Incompatibilities

While SKILL.md is interoperable, slash command formats differ across CLIs:

| CLI | Command Format | Location |
|-----|---------------|----------|
| Claude Code | Markdown (`.md`) with YAML frontmatter | `commands/*.md` |
| Gemini CLI | TOML (`.toml`) | `.gemini/commands/*.toml` |
| Codex CLI | Hardcoded / not user-extensible | — |
| Cursor | Rules-based (`.mdc`) | `.cursor/rules/*.mdc` |

Skills are the only component with a shared open format across all four tools.

## Distribution Strategy

### Symlinks for Multi-Tool Discovery

Since this repo's canonical skills live in `plugins/model-cli/skills/`, symlinks
provide zero-duplication discovery:

```
.codex/skills/{name} → ../../plugins/model-cli/skills/{name}
.gemini/skills/{name} → ../../plugins/model-cli/skills/{name}
```

**Cursor** does not need symlinks — it natively scans both `.claude/skills/` and
`.codex/skills/`.

**Claude Code** discovers skills through its plugin system (`plugins/model-cli/`),
so no additional symlinks are needed.

### Why Symlinks Work

- **Codex CLI**: Explicitly follows symlinks for repo-scoped skills
  ([`loader.rs:366-370`](https://github.com/openai/codex/blob/8b7f8af34/codex-rs/core/src/skills/loader.rs#L366-L370))
- **Gemini CLI**: Uses `glob()` which follows symlinks by default
- **Git**: Tracks symlinks as lightweight pointer files; works across clones

### Alternative Considered: `.agents/skills/`

Both Codex and Gemini scan `.agents/skills/`, which could serve as a single shared
directory. However, the tool-specific directories (`.codex/`, `.gemini/`) were chosen
for explicitness and to avoid the `.agents/` convention conflicting with other uses
of that namespace.

## Summary

| Aspect | Status |
|--------|--------|
| Single SKILL.md format | Works across all 4 CLIs |
| Unknown frontmatter fields | Silently ignored by all |
| Cross-tool distribution | Symlinks from `.codex/` and `.gemini/` |
| Cursor support | Free via `.claude/skills/` + `.codex/skills/` scanning |
| Command interoperability | Not possible (formats differ per tool) |
