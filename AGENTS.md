# AGENTS.md — claude-plugins

Project conventions and standards for AI-assisted development.

## Git Commit Standards

Format commit messages as:
```
Component/File(commit-type[Subcomponent/method]) Concise description

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
