# AGENTS.md — ai-workflow-skills

Project conventions and standards for AI-assisted development.

## Project Identity

This is a **public, third-party OpenSkills repository** providing language-agnostic
AI / agentic workflow skills for DX efficiency. Hosted on GitHub
([tony/ai-workflow-plugins](https://github.com/tony/ai-workflow-plugins)),
not affiliated with or endorsed by Anthropic, Google, or OpenAI.

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
- **ai(rules)**: AI convention files (AGENTS.md)

### Skill Component Naming

This repo contains OpenSkills SKILL.md files. Use the `ai(skill/*)` pattern:

- `ai(skill/commit)` — the `commit` skill specifically
- `ai(skill/multi-model-ask)` — the `multi-model-ask` skill specifically
- `ai(skills)` — changes spanning multiple skills
- `ai(rules)` — AGENTS.md or other AI convention files

When a change targets a specific named component, include it:
- `ai(claude[skill{commit}])` — the `commit` skill specifically
- `ai(claude[hook{PreToolUse}])` — a PreToolUse hook specifically
- `ai(claude[command{review-pr}])` — the `review-pr` command specifically

Examples:
```
ai(skill/commit) Add heredoc formatting for multi-line messages

why: Commit messages with body text need preserved newlines
what:
- Add heredoc template to commit skill prompt
- Include why/what body format in instructions
```

```
ai(skills) Update timeout defaults across multi-model skills

why: Previous defaults were too aggressive for large codebases
what:
- Increase ask default from 450s to 600s
- Increase review default from 900s to 1200s
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

## Skill Quality Standards

### SKILL.md Files

- Every `SKILL.md` **must** have YAML frontmatter with `name` and `description`
- Frontmatter must contain **only** `name` and `description` — no other fields
- Skills **must not** hardcode language-specific tool commands (e.g., `uv run pytest`,
  `npm test`, `cargo test`). Instead, reference "the project's test suite / quality checks
  as defined in AGENTS.md/CLAUDE.md"
- Descriptions should include "Use when..." trigger context explaining when to invoke

### Skill Directory Structure

```
skills/<name>/
├── SKILL.md             # skill definition (name + description frontmatter)
└── references/          # optional supporting documents
    └── infrastructure.md
```

### Language-Agnostic Design

Skills in this repository are designed to work with **any** programming language or
framework. Skills discover project-specific tooling by reading AGENTS.md / CLAUDE.md
at runtime rather than assuming a particular ecosystem. When listing examples of tools
or frameworks, present them as illustrative examples (e.g., in tables or lists), never
as hardcoded instructions.

### Accessible Code Blocks

- **One command per code block** — never combine multiple commands in a single
  fenced block; use separate blocks with explanatory text between them
- **No comments inside code blocks** — explanatory text goes outside as
  regular markdown, not as `#` comments inside the fence
