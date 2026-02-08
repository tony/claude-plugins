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
"""Marketplace management CLI for claude-plugins.

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
import typing as t
from pathlib import Path

import pydantic
import rich.console
import rich.table
import typer
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"
PLUGINS_DIR = REPO_ROOT / "plugins"

app = typer.Typer(help="Marketplace management CLI for claude-plugins.")
console = rich.console.Console()


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
    """

    name: str
    description: str
    version: str
    author: Author
    source: str
    category: str


class MarketplaceManifest(pydantic.BaseModel):
    """Top-level marketplace manifest schema.

    Examples
    --------
    >>> manifest = MarketplaceManifest(
    ...     name="test-marketplace",
    ...     description="Test",
    ...     owner=Author(name="Test"),
    ...     plugins=[],
    ... )
    >>> manifest.name
    'test-marketplace'
    """

    name: str
    description: str
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
        console.print(f"[red]Error:[/red] {MARKETPLACE_PATH} not found")
        raise SystemExit(1)
    raw = t.cast("dict[str, t.Any]", json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8")))
    return MarketplaceManifest.model_validate(raw)


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
            _ = PluginJson.model_validate(raw)
        except (json.JSONDecodeError, pydantic.ValidationError) as exc:
            errors.append(f"[{name}] Invalid plugin.json: {exc}")

    readme_path = plugin_dir / "README.md"
    if not readme_path.exists():
        errors.append(f"[{name}] Missing README.md")

    commands_dir = plugin_dir / "commands"
    if not commands_dir.exists():
        errors.append(f"[{name}] Missing commands/ directory")
    else:
        md_files = sorted(commands_dir.glob("*.md"))
        if not md_files:
            errors.append(f"[{name}] No .md files in commands/")
        for md_file in md_files:
            fm = parse_frontmatter(md_file)
            if fm is None:
                errors.append(f"[{name}] {md_file.name}: Missing YAML frontmatter")
            elif "description" not in fm:
                errors.append(f"[{name}] {md_file.name}: Frontmatter missing 'description'")

    return errors


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
        # Validate each plugin entry's source path
        for entry in manifest.plugins:
            source_path = REPO_ROOT / entry.source
            if not source_path.exists():
                errors.append(
                    f"Marketplace entry '{entry.name}': source path '{entry.source}' does not exist"
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
def sync(*, write: bool = False) -> None:
    """Compare discovered plugins with marketplace manifest.

    Parameters
    ----------
    write : bool
        If True, update marketplace.json with discovered plugins.
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

    # Remove missing plugins
    manifest.plugins = [e for e in manifest.plugins if e.name not in removals]

    # Write updated manifest
    raw_out: dict[str, t.Any] = manifest.model_dump(mode="json")
    raw_out["$schema"] = "https://anthropic.com/claude-code/marketplace.schema.json"
    output = json.dumps(raw_out, indent=2) + "\n"
    _ = MARKETPLACE_PATH.write_text(output, encoding="utf-8")
    console.print(f"\n[green]Updated {MARKETPLACE_PATH}[/green]")


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
