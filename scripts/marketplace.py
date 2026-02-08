#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pydantic>=2.0",
#     "rich>=13.0",
#     "typer>=0.15",
#     "pyyaml>=6.0",
# ]
# ///
"""Marketplace management CLI for ai-workflow-plugins.

Validates marketplace manifests, plugin structures, and command frontmatter.
Syncs the marketplace manifest with discovered plugin directories.

Examples
--------
Lint the marketplace:

>>> import subprocess
>>> result = subprocess.run(
...     ["python", "scripts/marketplace.py", "lint"],
...     capture_output=True,
...     text=True,
...     cwd=REPO_ROOT,
... )
>>> "errors" in result.stdout.lower() or result.returncode == 0
True
"""

from __future__ import annotations

import json
import shutil
import subprocess
import typing as t
from pathlib import Path

import pydantic
import rich.console
import rich.table
import typer
import yaml
from _private_path import PrivatePath  # pyright: ignore[reportImplicitRelativeImport]

RESERVED_MARKETPLACE_NAMES = frozenset(
    {
        "claude-code-marketplace",
        "claude-code-plugins",
        "claude-plugins-official",
        "anthropic-marketplace",
        "anthropic-plugins",
        "agent-skills",
        "life-sciences",
    }
)
"""Names explicitly reserved by the Claude Code plugin system."""

_PLUGIN_RELATED_WORDS = frozenset(
    {
        "plugin",
        "plugins",
        "marketplace",
        "tools",
        "extensions",
    }
)

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"
PLUGINS_DIR = REPO_ROOT / "plugins"

app = typer.Typer(
    help="Marketplace management CLI for ai-workflow-plugins.",
    invoke_without_command=True,
)
console = rich.console.Console()


@app.callback()
def _main(ctx: typer.Context) -> None:  # pyright: ignore[reportUnusedFunction]
    """Marketplace management CLI for ai-workflow-plugins."""
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


class Author(pydantic.BaseModel):
    """Author metadata for a plugin or marketplace.

    Examples
    --------
    >>> Author(name="Test", email="test@example.com")
    Author(name='Test', email='test@example.com', url=None)
    """

    name: str
    email: str | None = None
    url: str | None = None


VALID_CATEGORIES = (
    "database",
    "deployment",
    "design",
    "development",
    "learning",
    "monitoring",
    "productivity",
    "security",
    "testing",
)
"""Valid plugin marketplace categories (alphabetical)."""

Category = t.Literal[
    "database",
    "deployment",
    "design",
    "development",
    "learning",
    "monitoring",
    "productivity",
    "security",
    "testing",
]


class PluginEntry(pydantic.BaseModel):
    """A plugin entry in the marketplace manifest.

    Examples
    --------
    >>> entry = PluginEntry(
    ...     name="test",
    ...     description="A test plugin",
    ...     version="1.0.0",
    ...     author=Author(name="Test"),
    ...     source="./plugins/test",
    ...     category="development",
    ... )
    >>> entry.name
    'test'

    Invalid categories are rejected:

    >>> try:
    ...     PluginEntry(
    ...         name="bad",
    ...         description="Bad",
    ...         version="1.0.0",
    ...         author=Author(name="Test"),
    ...         source="./plugins/bad",
    ...         category="invalid-category",
    ...     )
    ... except pydantic.ValidationError:
    ...     print("rejected")
    rejected
    """

    name: str
    description: str
    version: str
    author: Author
    source: str
    category: Category
    tags: list[str] | None = None
    homepage: str | None = None
    repository: str | None = None
    license: str | None = None
    keywords: list[str] | None = None
    strict: bool | None = None


class MarketplaceMetadata(pydantic.BaseModel):
    """Marketplace metadata block (required by ``claude plugin validate``).

    Examples
    --------
    >>> MarketplaceMetadata(description="Test marketplace")
    MarketplaceMetadata(description='Test marketplace')
    """

    description: str


class MarketplaceManifest(pydantic.BaseModel):
    """Top-level marketplace manifest schema.

    Examples
    --------
    >>> manifest = MarketplaceManifest(
    ...     name="test-marketplace",
    ...     description="Test",
    ...     metadata=MarketplaceMetadata(description="Test"),
    ...     owner=Author(name="Test"),
    ...     plugins=[],
    ... )
    >>> manifest.name
    'test-marketplace'
    """

    name: str
    description: str
    metadata: MarketplaceMetadata
    owner: Author
    plugins: list[PluginEntry]


class PluginJson(pydantic.BaseModel):
    """Individual plugin.json schema.

    Examples
    --------
    >>> pj = PluginJson(name="test", description="A test plugin")
    >>> pj.name
    'test'
    """

    name: str
    description: str
    author: Author | None = None
    version: str | None = None
    homepage: str | None = None
    repository: str | None = None
    license: str | None = None
    keywords: list[str] | None = None


def load_marketplace() -> MarketplaceManifest:
    """Load and validate the marketplace manifest.

    Returns
    -------
    MarketplaceManifest
        The parsed and validated manifest.

    Raises
    ------
    SystemExit
        If the manifest file is missing or invalid.
    """
    if not MARKETPLACE_PATH.exists():
        console.print(f"[red]Error:[/red] {PrivatePath(MARKETPLACE_PATH)} not found")
        raise SystemExit(1)
    raw = t.cast("dict[str, t.Any]", json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8")))
    return MarketplaceManifest.model_validate(raw)


def validate_marketplace_name(name: str) -> list[str]:
    """Check a marketplace name against reserved name restrictions.

    Returns a list of error messages (empty if the name is valid).

    Parameters
    ----------
    name : str
        The marketplace name to validate.

    Returns
    -------
    list[str]
        Error messages for any violations found.

    Examples
    --------
    Reserved names are rejected:

    >>> validate_marketplace_name("claude-plugins-official")
    ["Marketplace name 'claude-plugins-official' is reserved"]

    Names containing 'claude' with plugin-related words are rejected:

    >>> errs = validate_marketplace_name("claude-plugins")
    >>> len(errs) == 1 and "impersonates" in errs[0]
    True

    Names containing 'anthropic' are rejected:

    >>> errs = validate_marketplace_name("anthropic-tools-v2")
    >>> len(errs) == 1 and "anthropic" in errs[0]
    True

    Non-reserved names pass:

    >>> validate_marketplace_name("ai-workflow-plugins")
    []
    """
    errors: list[str] = []

    if name in RESERVED_MARKETPLACE_NAMES:
        errors.append(f"Marketplace name '{name}' is reserved")
        return errors

    if "anthropic" in name:
        errors.append(
            f"Marketplace name '{name}' impersonates an official marketplace (contains 'anthropic')"
        )
        return errors

    if "official" in name:
        errors.append(
            f"Marketplace name '{name}' impersonates an official marketplace (contains 'official')"
        )
        return errors

    if "claude" in name:
        for word in _PLUGIN_RELATED_WORDS:
            if word in name:
                msg = (
                    f"Marketplace name '{name}' impersonates an official"
                    f" marketplace (contains 'claude' with '{word}')"
                )
                errors.append(msg)
                return errors

    return errors


def discover_plugins() -> list[Path]:
    """Find all plugin directories under plugins/.

    Returns
    -------
    list[Path]
        Sorted list of directories containing .claude-plugin/plugin.json.
    """
    if not PLUGINS_DIR.exists():
        return []
    return sorted(
        d
        for d in PLUGINS_DIR.iterdir()
        if d.is_dir() and (d / ".claude-plugin" / "plugin.json").exists()
    )


def parse_frontmatter(path: Path) -> dict[str, t.Any] | None:
    r"""Parse YAML frontmatter from a markdown file.

    Parameters
    ----------
    path : Path
        Path to the markdown file.

    Returns
    -------
    dict[str, Any] or None
        Parsed frontmatter dict, or None if no frontmatter found.

    Examples
    --------
    >>> from pathlib import Path
    >>> import tempfile, os
    >>> d = tempfile.mkdtemp()
    >>> p = Path(d) / "test.md"
    >>> _ = p.write_text("---\ndescription: hello\n---\n# Title\n")
    >>> result = parse_frontmatter(p)
    >>> result["description"]
    'hello'
    >>> p2 = Path(d) / "no_fm.md"
    >>> _ = p2.write_text("# No frontmatter\n")
    >>> parse_frontmatter(p2) is None
    True
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    fm_text = text[3:end].strip()
    loaded = t.cast("object", yaml.safe_load(fm_text))
    if isinstance(loaded, dict):
        return t.cast("dict[str, t.Any]", loaded)
    return None


def _validate_agents_dir(plugin_name: str, agents_dir: Path) -> list[str]:
    """Validate agents/*.md frontmatter in a plugin directory."""
    errors: list[str] = []
    for md_file in sorted(agents_dir.glob("*.md")):
        fm = parse_frontmatter(md_file)
        if fm is None:
            errors.append(f"[{plugin_name}] agents/{md_file.name}: Missing YAML frontmatter")
        else:
            errors.extend(
                f"[{plugin_name}] agents/{md_file.name}: Frontmatter missing '{field}'"
                for field in ("name", "description")
                if field not in fm
            )
    return errors


def _validate_skills_dir(plugin_name: str, skills_dir: Path) -> list[str]:
    """Validate skills/*/SKILL.md frontmatter in a plugin directory."""
    errors: list[str] = []
    for skill_subdir in sorted(d for d in skills_dir.iterdir() if d.is_dir()):
        skill_md = skill_subdir / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"[{plugin_name}] skills/{skill_subdir.name}/: Missing SKILL.md")
            continue
        fm = parse_frontmatter(skill_md)
        if fm is None:
            errors.append(
                f"[{plugin_name}] skills/{skill_subdir.name}/SKILL.md: Missing YAML frontmatter"
            )
        else:
            prefix = f"[{plugin_name}] skills/{skill_subdir.name}/SKILL.md"
            errors.extend(
                f"{prefix}: Frontmatter missing '{field}'"
                for field in ("name", "description")
                if field not in fm
            )
    return errors


def _validate_mcp_json(plugin_name: str, path: Path) -> list[str]:
    """Validate .mcp.json structural requirements.

    Parameters
    ----------
    plugin_name : str
        Plugin name for error messages.
    path : Path
        Path to the .mcp.json file.

    Returns
    -------
    list[str]
        Error messages (empty if valid).

    Examples
    --------
    >>> from pathlib import Path
    >>> import tempfile
    >>> d = tempfile.mkdtemp()
    >>> p = Path(d) / ".mcp.json"
    >>> _ = p.write_text('{"server": {"type": "http", "url": "http://localhost"}}')
    >>> _validate_mcp_json("test", p)
    []

    Non-dict top-level is rejected:

    >>> _ = p.write_text('[]')
    >>> _validate_mcp_json("test", p)
    ['[test] .mcp.json: top-level value must be an object']

    Non-dict server entries are rejected:

    >>> _ = p.write_text('{"server": "bad"}')
    >>> _validate_mcp_json("test", p)
    ["[test] .mcp.json: server entry 'server' must be an object"]
    """
    errors: list[str] = []
    try:
        data = t.cast("object", json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as exc:
        errors.append(f"[{plugin_name}] .mcp.json: invalid JSON: {exc}")
        return errors

    if not isinstance(data, dict):
        errors.append(f"[{plugin_name}] .mcp.json: top-level value must be an object")
        return errors

    servers = t.cast("dict[str, object]", data)
    for key, value in servers.items():
        if not isinstance(value, dict):
            errors.append(f"[{plugin_name}] .mcp.json: server entry '{key}' must be an object")
    return errors


def _validate_lsp_json(plugin_name: str, path: Path) -> list[str]:
    """Validate .lsp.json structural requirements.

    Parameters
    ----------
    plugin_name : str
        Plugin name for error messages.
    path : Path
        Path to the .lsp.json file.

    Returns
    -------
    list[str]
        Error messages (empty if valid).

    Examples
    --------
    >>> from pathlib import Path
    >>> import tempfile
    >>> d = tempfile.mkdtemp()
    >>> p = Path(d) / ".lsp.json"
    >>> data = '{"pyright": {"command": "pyright-langserver",'
    >>> data += ' "extensionToLanguage": {".py": "python"}}}'
    >>> _ = p.write_text(data)
    >>> _validate_lsp_json("test", p)
    []

    Non-dict top-level is rejected:

    >>> _ = p.write_text('[]')
    >>> _validate_lsp_json("test", p)
    ['[test] .lsp.json: top-level value must be an object']

    Missing required fields are reported:

    >>> _ = p.write_text('{"pyright": {"command": "pyright-langserver"}}')
    >>> _validate_lsp_json("test", p)
    ["[test] .lsp.json: server 'pyright' missing required field 'extensionToLanguage'"]

    >>> _ = p.write_text('{"pyright": {"extensionToLanguage": {".py": "python"}}}')
    >>> _validate_lsp_json("test", p)
    ["[test] .lsp.json: server 'pyright' missing required field 'command'"]
    """
    errors: list[str] = []
    try:
        data = t.cast("object", json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as exc:
        errors.append(f"[{plugin_name}] .lsp.json: invalid JSON: {exc}")
        return errors

    if not isinstance(data, dict):
        errors.append(f"[{plugin_name}] .lsp.json: top-level value must be an object")
        return errors

    servers = t.cast("dict[str, object]", data)
    for key, value in servers.items():
        if not isinstance(value, dict):
            errors.append(f"[{plugin_name}] .lsp.json: server entry '{key}' must be an object")
            continue
        errors.extend(
            f"[{plugin_name}] .lsp.json: server '{key}' missing required field '{field}'"
            for field in ("command", "extensionToLanguage")
            if field not in value
        )
    return errors


def validate_plugin_dir(plugin_dir: Path) -> list[str]:
    """Validate a single plugin directory structure.

    Parameters
    ----------
    plugin_dir : Path
        Path to the plugin directory.

    Returns
    -------
    list[str]
        List of error messages (empty if valid).
    """
    errors: list[str] = []
    name = plugin_dir.name

    plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"
    if not plugin_json_path.exists():
        errors.append(f"[{name}] Missing .claude-plugin/plugin.json")
    else:
        try:
            raw = t.cast(
                "dict[str, t.Any]",
                json.loads(plugin_json_path.read_text(encoding="utf-8")),
            )
            pj = PluginJson.model_validate(raw)
            if pj.name != name:
                errors.append(
                    f"[{name}] plugin.json name '{pj.name}' does not match directory name '{name}'"
                )
        except (json.JSONDecodeError, pydantic.ValidationError) as exc:
            errors.append(f"[{name}] Invalid plugin.json: {exc}")

    readme_path = plugin_dir / "README.md"
    if not readme_path.exists():
        errors.append(f"[{name}] Missing README.md")

    # Check for at least one component directory or config file
    component_dirs = ["commands", "agents", "skills", "hooks"]
    config_files = [".mcp.json", ".lsp.json"]
    has_component = any((plugin_dir / d).exists() for d in component_dirs) or any(
        (plugin_dir / f).exists() for f in config_files
    )
    if not has_component:
        msg = f"[{name}] No component directory or config file found"
        errors.append(msg)

    # Validate commands/*.md frontmatter
    commands_dir = plugin_dir / "commands"
    if commands_dir.exists():
        md_files = sorted(commands_dir.glob("*.md"))
        if not md_files:
            errors.append(f"[{name}] No .md files in commands/")
        for md_file in md_files:
            fm = parse_frontmatter(md_file)
            if fm is None:
                errors.append(f"[{name}] commands/{md_file.name}: Missing YAML frontmatter")
            elif "description" not in fm:
                errors.append(
                    f"[{name}] commands/{md_file.name}: Frontmatter missing 'description'"
                )

    # Validate agents/*.md and skills/*/SKILL.md frontmatter
    agents_dir = plugin_dir / "agents"
    if agents_dir.exists():
        errors.extend(_validate_agents_dir(name, agents_dir))

    skills_dir = plugin_dir / "skills"
    if skills_dir.exists():
        errors.extend(_validate_skills_dir(name, skills_dir))

    # Validate hooks/hooks.json exists when hooks/ is present
    hooks_dir = plugin_dir / "hooks"
    if hooks_dir.exists():
        hooks_json = hooks_dir / "hooks.json"
        if not hooks_json.exists():
            errors.append(f"[{name}] hooks/ exists but missing hooks.json")

    # Validate .mcp.json structure
    mcp_json_path = plugin_dir / ".mcp.json"
    if mcp_json_path.exists():
        errors.extend(_validate_mcp_json(name, mcp_json_path))

    # Validate .lsp.json structure
    lsp_json_path = plugin_dir / ".lsp.json"
    if lsp_json_path.exists():
        errors.extend(_validate_lsp_json(name, lsp_json_path))

    return errors


def _run_claude_validate(path: Path) -> tuple[list[str], list[str]]:
    """Run ``claude plugin validate`` and return (errors, warnings).

    Returns empty lists if the CLI is not available.

    Parameters
    ----------
    path : Path
        Path to validate (marketplace root or plugin directory).

    Returns
    -------
    tuple[list[str], list[str]]
        (errors, warnings) extracted from validate output.
    """
    if shutil.which("claude") is None:
        return [], []
    result = subprocess.run(  # noqa: S603
        ["claude", "plugin", "validate", str(path)],  # noqa: S607
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    marker = "\u276f"
    findings = [
        line.strip().removeprefix(marker).strip()
        for line in result.stdout.splitlines()
        if marker in line
    ]
    if result.returncode != 0:
        return [f"claude validate: {f}" for f in findings], []
    return [], [f"claude validate: {f}" for f in findings]


def _lint_claude_validate() -> tuple[list[str], list[str]]:
    """Run ``claude plugin validate`` on the repo and each plugin, printing status."""
    if shutil.which("claude") is None:
        console.print("\n[dim]Skipping claude plugin validate (CLI not found)[/dim]")
        return [], []

    console.print("\n[bold]Running claude plugin validate...[/bold]")
    all_errors: list[str] = []
    all_warnings: list[str] = []
    for path in [REPO_ROOT, *discover_plugins()]:
        ve, vw = _run_claude_validate(path)
        all_errors.extend(ve)
        all_warnings.extend(vw)
    if not all_errors:
        console.print("  [green]OK[/green]")
    return all_errors, all_warnings


@app.command()
def lint() -> None:
    """Validate the marketplace manifest and all plugin directories."""
    errors: list[str] = []
    warnings: list[str] = []

    # Validate marketplace manifest
    console.print("[bold]Validating marketplace manifest...[/bold]")
    try:
        manifest = load_marketplace()
        console.print(f"  Manifest: [green]OK[/green] ({len(manifest.plugins)} plugins)")
    except SystemExit:
        errors.append("Marketplace manifest not found or invalid")
        manifest = None

    if manifest is not None:
        # Validate marketplace name against reserved names
        name_errors = validate_marketplace_name(manifest.name)
        errors.extend(name_errors)

        # Validate each plugin entry's source path
        for entry in manifest.plugins:
            source_path = REPO_ROOT / entry.source
            if not source_path.exists():
                errors.append(
                    f"Marketplace entry '{entry.name}': source path '{entry.source}' does not exist"
                )

        # Check for duplicate plugin names
        seen_names: dict[str, int] = {}
        for entry in manifest.plugins:
            seen_names[entry.name] = seen_names.get(entry.name, 0) + 1
        for dup_name, count in sorted(seen_names.items()):
            if count > 1:
                errors.append(
                    f"Duplicate plugin name '{dup_name}' appears {count} times in marketplace.json"
                )

        # Validate each plugin directory
        console.print("\n[bold]Validating plugin directories...[/bold]")
        discovered = discover_plugins()
        for plugin_dir in discovered:
            plugin_errors = validate_plugin_dir(plugin_dir)
            if plugin_errors:
                errors.extend(plugin_errors)
            else:
                console.print(f"  {plugin_dir.name}: [green]OK[/green]")

        # Check for plugins not in marketplace
        manifest_names = {e.name for e in manifest.plugins}
        discovered_names = {d.name for d in discovered}
        undiscovered = discovered_names - manifest_names
        warnings.extend(
            f"Plugin '{name}' exists in plugins/ but is not listed in marketplace.json"
            for name in sorted(undiscovered)
        )

    # Run claude plugin validate if CLI is available
    cli_errors, cli_warnings = _lint_claude_validate()
    errors.extend(cli_errors)
    warnings.extend(cli_warnings)

    # Report results
    console.print()
    if warnings:
        for warning in warnings:
            console.print(f"[yellow]Warning:[/yellow] {warning}")

    if errors:
        for error in errors:
            console.print(f"[red]Error:[/red] {error}")
        console.print(f"\n[red bold]{len(errors)} error(s) found.[/red bold]")
        raise SystemExit(1)

    console.print("[green bold]0 errors found.[/green bold]")


@app.command()
def sync(*, write: bool = False, check: bool = False) -> None:
    """Compare discovered plugins with marketplace manifest.

    Parameters
    ----------
    write : bool
        If True, update marketplace.json with discovered plugins.
    check : bool
        If True, exit with code 1 when drift is detected (for CI).

    Examples
    --------
    The ``--check`` flag is designed for CI pipelines:

    >>> import subprocess
    >>> result = subprocess.run(
    ...     ["python", "scripts/marketplace.py", "sync", "--check"],
    ...     capture_output=True,
    ...     text=True,
    ...     cwd=REPO_ROOT,
    ... )
    >>> result.returncode == 0  # 0 means in sync
    True
    """
    manifest = load_marketplace()
    discovered = discover_plugins()

    manifest_names = {e.name for e in manifest.plugins}
    discovered_names = {d.name for d in discovered}

    additions = sorted(discovered_names - manifest_names)
    removals = sorted(manifest_names - discovered_names)

    if not additions and not removals:
        console.print("[green]Marketplace manifest is in sync with plugins/.[/green]")
        return

    table = rich.table.Table(title="Sync Report")
    table.add_column("Status", style="bold")
    table.add_column("Plugin")

    for name in additions:
        table.add_row("[green]+ Add[/green]", name)
    for name in removals:
        table.add_row("[red]- Remove[/red]", name)

    console.print(table)

    if check:
        msg = (
            "\n[red bold]Marketplace manifest is out of sync.[/red bold]"
            " Run 'sync --write' to update."
        )
        console.print(msg)
        raise SystemExit(1)

    if not write:
        console.print("\nRun with [bold]--write[/bold] to update marketplace.json.")
        return

    # Add new plugins
    for name in additions:
        plugin_dir = PLUGINS_DIR / name
        plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"
        raw = t.cast(
            "dict[str, t.Any]",
            json.loads(plugin_json_path.read_text(encoding="utf-8")),
        )
        plugin_meta = PluginJson.model_validate(raw)
        new_entry = PluginEntry(
            name=plugin_meta.name,
            description=plugin_meta.description,
            version=plugin_meta.version or "1.0.0",
            author=plugin_meta.author or manifest.owner,
            source=f"./plugins/{name}",
            category="development",
        )
        manifest.plugins.append(new_entry)
        msg = (
            f"[yellow]Warning:[/yellow] Plugin '{name}' defaulting to"
            " category='development' — update marketplace.json if needed"
        )
        console.print(msg)

    # Remove missing plugins
    manifest.plugins = [e for e in manifest.plugins if e.name not in removals]

    # Write updated manifest
    raw_out: dict[str, t.Any] = manifest.model_dump(mode="json")
    raw_out["$schema"] = "https://anthropic.com/claude-code/marketplace.schema.json"
    output = json.dumps(raw_out, indent=2) + "\n"
    _ = MARKETPLACE_PATH.write_text(output, encoding="utf-8")
    console.print(f"\n[green]Updated {PrivatePath(MARKETPLACE_PATH)}[/green]")


@app.command(name="check-outdated")
def check_outdated() -> None:
    """Compare versions between plugin.json and marketplace entries."""
    manifest = load_marketplace()

    table = rich.table.Table(title="Version Comparison")
    table.add_column("Plugin")
    table.add_column("Marketplace Version")
    table.add_column("plugin.json Version")
    table.add_column("Status")

    has_mismatch = False

    for entry in manifest.plugins:
        plugin_dir = PLUGINS_DIR / entry.name
        plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"

        if not plugin_json_path.exists():
            table.add_row(entry.name, entry.version, "[red]missing[/red]", "[red]ERROR[/red]")
            has_mismatch = True
            continue

        raw = t.cast(
            "dict[str, t.Any]",
            json.loads(plugin_json_path.read_text(encoding="utf-8")),
        )
        plugin_meta = PluginJson.model_validate(raw)
        local_version = plugin_meta.version or "(not set)"

        if plugin_meta.version != entry.version:
            table.add_row(
                entry.name,
                entry.version,
                local_version,
                "[yellow]MISMATCH[/yellow]",
            )
            has_mismatch = True
        else:
            table.add_row(entry.name, entry.version, local_version, "[green]OK[/green]")

    console.print(table)

    if has_mismatch:
        console.print("\n[yellow]Version mismatches found.[/yellow]")
    else:
        console.print("\n[green]All versions match.[/green]")


if __name__ == "__main__":
    app()
