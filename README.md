# ai-workflow-plugins

A third-party [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces.md)
providing language-agnostic AI / agentic workflow plugins for DX efficiency.

> **Warning:** Review plugins before installing. Anthropic does not control plugin
> contents and cannot verify they work as intended.

**Repository:** [tony/ai-workflow-plugins](https://github.com/tony/ai-workflow-plugins)

## Plugins

| Plugin | Category | Description |
|--------|----------|-------------|
| [commit](plugins/commit/) | Development | Create git commits following project conventions with format enforcement and safety checks |
| [multi-model](plugins/multi-model/) | Development | Run prompts across Claude, Gemini, and GPT in parallel — plan, execute, review, and synthesize |
| [rebase](plugins/rebase/) | Development | Automated rebase onto trunk with conflict prediction, resolution, and quality gate verification |
| [changelog](plugins/changelog/) | Productivity | Generate categorized changelog entries from branch commits and PR context |
| [tdd](plugins/tdd/) | Testing | TDD bug-fix workflow — reproduce bugs as failing tests, find root cause, fix, and verify |

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

You can also browse available plugins with `/plugin > Discover`.

Then install any plugin:

```console
/plugin install commit@ai-workflow-plugins
```

```console
/plugin install multi-model@ai-workflow-plugins
```

```console
/plugin install rebase@ai-workflow-plugins
```

```console
/plugin install changelog@ai-workflow-plugins
```

```console
/plugin install tdd@ai-workflow-plugins
```

## Design Philosophy

Every plugin in this repository is **language-agnostic**. Commands do not hardcode
language-specific tools like `pytest`, `jest`, `cargo test`, or `ruff`. Instead, they
reference the project's own conventions by reading `AGENTS.md` or `CLAUDE.md` at
runtime to discover:

- How to run the test suite
- How to run linters and formatters
- How to run type checkers
- What commit message format to use
- What test patterns to follow

This means the same plugin works whether your project uses Python, TypeScript, Rust, Go,
or any other language.

## Development

Scripts use [uv](https://docs.astral.sh/uv/) to manage Python dependencies.

Install uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

or:

```bash
wget -qO- https://astral.sh/uv/install.sh | sh
```

See [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/) for
other methods.

### Lint and validate

```bash
uv run ./scripts/marketplace.py lint
```

### Sync marketplace manifest with plugin directories

Dry-run:

```bash
uv run ./scripts/marketplace.py sync
```

Write changes to marketplace.json:

```bash
uv run ./scripts/marketplace.py sync --write
```

### Check for outdated entries

```bash
uv run ./scripts/marketplace.py check-outdated
```

### Code quality for scripts

Lint:

```bash
uv run ruff check ./scripts/
```

Format check:

```bash
uv run ruff format --check ./scripts/
```

Type check:

```bash
uv run basedpyright ./scripts/
```

## Documentation

See the [official Claude Code plugin docs](https://docs.anthropic.com/en/docs/claude-code/plugins) for
authoring guides, component schemas, and marketplace publishing.

## License

MIT
