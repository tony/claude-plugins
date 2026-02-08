# AGENTS.md — claude-plugins

Project conventions and standards for AI-assisted development.

## Official Documentation References

These docs define the Claude Code plugin system and should be consulted for spec details:

- [Plugins overview](https://code.claude.com/docs/en/plugins.md) — plugin lifecycle, installation, discovery
- [Plugin reference](https://code.claude.com/docs/en/plugins-reference.md) — component types, frontmatter schemas, directory structure
- [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces.md) — marketplace.json schema, source types, publishing
- [Sub-agents](https://code.claude.com/docs/en/sub-agents.md) — agent frontmatter, delegation patterns, tool restrictions
- [Agent teams](https://code.claude.com/docs/en/agent-teams.md) — multi-agent coordination (experimental)

## Git Commit Standards

Format commit messages as:
```
Scope(type[detail]) concise description

why: Explanation of necessity or impact.
what:
- Specific technical changes made
- Focused on a single topic
```

Common commit types:
- **feat**: New features or enhancements
- **fix**: Bug fixes
- **refactor**: Code restructuring without functional change
- **docs**: Documentation updates
- **chore**: Maintenance (dependencies, tooling, config)
- **test**: Test-related updates
- **style**: Code style and formatting
- **ai(rules[AGENTS])**: AI rule updates
- **ai(claude[rules])**: Claude Code rules (CLAUDE.md)
- **ai(claude[command])**: Claude Code command changes

### Project Component Naming

This repo contains Claude Code plugins, commands, skills, hooks, and agents. Use the
`ai(claude[...])` component pattern:

- `ai(claude[plugin])` — plugin manifest, structure, or multi-component changes
- `ai(claude[plugins])` — changes spanning multiple plugins
- `ai(claude[command])` — a single slash command
- `ai(claude[commands])` — changes spanning multiple commands
- `ai(claude[skill])` — a single skill
- `ai(claude[skills])` — changes spanning multiple skills
- `ai(claude[hook])` — a single hook
- `ai(claude[hooks])` — changes spanning multiple hooks
- `ai(claude[agent])` — a single agent definition
- `ai(claude[agents])` — changes spanning multiple agents
- `ai(rules)` — AGENTS.md or other AI convention files

When a change targets a specific named component, include it:
- `ai(claude[skill/commit])` — the `commit` skill specifically
- `ai(claude[hook/PreToolUse])` — a PreToolUse hook specifically
- `ai(claude[command/review-pr])` — the `review-pr` command specifically

Examples:
```
ai(claude[skill/commit]) Add heredoc formatting for multi-line messages

why: Commit messages with body text need preserved newlines
what:
- Add heredoc template to commit skill prompt
- Include why/what body format in instructions
```

```
ai(claude[hooks]) Add PreToolUse validation for Bash commands

why: Prevent accidental destructive shell commands
what:
- Add PreToolUse hook to intercept Bash tool calls
- Block rm -rf and git push --force without confirmation
```

```
ai(rules) Add project-specific commit component conventions

why: Claude Code plugins need distinct component prefixes
what:
- Add ai(claude[...]) naming scheme for plugins, commands, skills, hooks
- Include examples for single and multi-component changes
```

For multi-line commits, use heredoc to preserve formatting:
```bash
git commit -m "$(cat <<'EOF'
feat(Component[method]) add feature description

why: Explanation of the change.
what:
- First change
- Second change
EOF
)"
```

## Plugin Quality Standards

### Command Files

- Every command `.md` file **must** have YAML frontmatter with at least a `description` field
- Commands **must not** hardcode language-specific tool commands (e.g., `uv run pytest`,
  `npm test`, `cargo test`). Instead, reference "the project's test suite / quality checks
  as defined in AGENTS.md/CLAUDE.md"
- Frontmatter `allowed-tools` should use bare tool names (e.g., `Bash`) rather than
  language-specific patterns (e.g., `Bash(uv run:*)`) so commands work across any project

### Plugin Directory Structure

Every plugin directory under `plugins/` must contain `.claude-plugin/plugin.json` and
`README.md`. Beyond that, include any combination of component directories:

```
plugins/<name>/
├── .claude-plugin/
│   └── plugin.json      # name, description, author (required)
├── README.md            # usage docs, prerequisites, component reference
├── commands/            # slash commands (*.md with YAML frontmatter)
├── agents/              # sub-agents (*.md with name, description, tools)
├── skills/              # skills (skill-name/SKILL.md)
├── hooks/               # hooks (hooks.json)
├── .mcp.json            # MCP server configuration
└── .lsp.json            # LSP server configuration
```

At least one component directory (`commands/`, `agents/`, `skills/`, or `hooks/`) or
configuration file (`.mcp.json`, `.lsp.json`) is expected.

### Component Frontmatter Schemas

Each component type has specific frontmatter requirements:

**Commands** (`commands/*.md`):
- `description` (required) — shown in `/` menu
- `allowed-tools` (optional) — tool access list (bare names, e.g. `Bash`)
- `argument-hint` (optional) — placeholder text for command argument
- `model` (optional) — model override for this command
- `disable-model-invocation` (optional) — if true, command runs without model invocation

**Agents** (`agents/*.md`):
- `name` (required) — agent identifier (lowercase letters and hyphens)
- `description` (required) — when to delegate to this agent; include `<example>` blocks
- `tools` (optional) — comma-separated tool access list
- `disallowedTools` (optional) — comma-separated tools to deny
- `model` (optional) — `sonnet`, `opus`, `haiku`, or `inherit`
- `permissionMode` (optional) — `default`, `acceptEdits`, `delegate`, `dontAsk`, `bypassPermissions`, `plan`
- `maxTurns` (optional) — max agentic turns before agent stops
- `skills` (optional) — skill names to preload into agent context
- `mcpServers` (optional) — MCP servers available to this agent
- `hooks` (optional) — lifecycle hooks scoped to this agent
- `memory` (optional) — persistent memory scope: `user`, `project`, `local`
- `color` (optional) — visual indicator: `yellow`, `green`, `red`, `cyan`, `pink`

**Skills** (`skills/*/SKILL.md`):
- `name` (required) — skill display name
- `description` (required) — describes when and how to invoke the skill
- `version` (optional) — skill version
- `tools` (optional) — comma-separated tool access list
- `disallowedTools` (optional) — comma-separated tools to deny
- `context` (optional) — agent context mode
- `disable-model-invocation` (optional) — if true, runs without model invocation

**Hooks** (`hooks/hooks.json`):
```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Write|Edit", "hooks": [{ "type": "command", "command": "..." }] }
    ]
  }
}
```
- Events: `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, `UserPromptSubmit`,
  `SessionStart`, `SessionEnd`, `PreCompact`, `Notification`
- Hook types: `command` (shell script), `prompt` (LLM evaluation), `agent` (agentic verifier)
- Use `${CLAUDE_PLUGIN_ROOT}` for portable paths in command hooks

### Marketplace Manifest

- Located at `.claude-plugin/marketplace.json`
- Must reference every plugin under `plugins/` with a valid `source` path
- Each entry requires: `name`, `description`, `version`, `author`, `source`, `category`
- Valid categories: `development`, `productivity`, `testing`, `security`, `design`,
  `database`, `deployment`, `monitoring`, `learning`

### Language-Agnostic Design

Plugins in this repository are designed to work with **any** programming language or
framework. Commands discover project-specific tooling by reading AGENTS.md / CLAUDE.md
at runtime rather than assuming a particular ecosystem. When listing examples of tools
or frameworks, present them as illustrative examples (e.g., in tables or lists), never
as hardcoded instructions.
