#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0",
#     "typer>=0.15",
# ]
# ///
"""E2E plugin lifecycle tests for ai-workflow-plugins.

Runs the full Claude plugin CLI lifecycle in an isolated sandbox:
validate -> marketplace add -> install -> disable/enable -> uninstall -> marketplace remove.

Sandboxing: Sets ``HOME`` to a temp directory so ``claude`` reads all config
from ``$HOME/.claude/`` without touching the real user config.

Examples
--------
Test with local marketplace source (default):

    uv run scripts/e2e.py

Test with GitHub source:

    uv run scripts/e2e.py --source github

Test both sources:

    uv run scripts/e2e.py --source both
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import typing as t
from pathlib import Path

import rich.console
import typer
from _private_path import PrivatePath  # pyright: ignore[reportImplicitRelativeImport]

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE_NAME = "ai-workflow-plugins"
GITHUB_SOURCE = "tony/ai-workflow-plugins"
PLUGINS = ["multi-model", "rebase", "changelog", "tdd"]

app = typer.Typer(help="E2E plugin lifecycle tests for ai-workflow-plugins.")
console = rich.console.Console()

Source = t.Literal["local", "github", "both"]

TestCase = tuple[str, t.Callable[[], None]]


class TestFailureError(Exception):
    """Raised when a test assertion fails."""


def _run_claude(args: list[str], sandbox: Path) -> subprocess.CompletedProcess[str]:
    """Run a ``claude`` CLI command with HOME set to *sandbox*.

    Parameters
    ----------
    args : list[str]
        Arguments to pass after ``claude``.
    sandbox : Path
        Temporary home directory for isolation.

    Returns
    -------
    subprocess.CompletedProcess[str]
        The completed process result.
    """
    env = {**os.environ, "HOME": str(sandbox)}
    return subprocess.run(  # noqa: S603
        ["claude", *args],  # noqa: S607
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
        check=False,
    )


def _assert(condition: bool, msg: str) -> None:
    """Assert *condition* is truthy, raising `TestFailureError` on failure."""
    if not condition:
        raise TestFailureError(msg)


def _pass(label: str) -> None:
    console.print(f"  [green]✔[/green] {label}")


def _fail(label: str, detail: str) -> None:
    console.print(f"  [red]✘[/red] {label}")
    console.print(f"    [dim]{detail}[/dim]")


def _run_test(label: str, fn: t.Callable[[], None]) -> bool:
    """Run a single test, print pass/fail, return success bool."""
    try:
        fn()
        _pass(label)
    except TestFailureError as exc:
        _fail(label, str(exc))
        return False
    except subprocess.TimeoutExpired:
        _fail(label, "Command timed out (120s)")
        return False
    return True


# ---------------------------------------------------------------------------
# Test case builders
# ---------------------------------------------------------------------------


def _test_validate(sandbox: Path) -> list[TestCase]:
    """Build validate test cases."""
    tests: list[TestCase] = []

    def _validate_marketplace() -> None:
        r = _run_claude(["plugin", "validate", str(REPO_ROOT)], sandbox)
        _assert(r.returncode == 0, f"exit {r.returncode}: {r.stdout}{r.stderr}")
        _assert("error" not in r.stdout.lower(), f"Unexpected errors: {r.stdout}")

    tests.append(("validate marketplace", _validate_marketplace))

    for plugin in PLUGINS:
        plugin_path = str(REPO_ROOT / "plugins" / plugin)

        def _validate_plugin(p: str = plugin_path, name: str = plugin) -> None:
            r = _run_claude(["plugin", "validate", p], sandbox)
            _assert(r.returncode == 0, f"exit {r.returncode}: {r.stdout}{r.stderr}")
            _assert("error" not in r.stdout.lower(), f"Unexpected errors in {name}: {r.stdout}")

        tests.append((f"validate plugin: {plugin}", _validate_plugin))

    return tests


def _test_marketplace_add(sandbox: Path, source: str) -> list[TestCase]:
    """Build marketplace add/list test cases."""
    tests: list[TestCase] = []

    def _marketplace_add() -> None:
        r = _run_claude(["plugin", "marketplace", "add", source], sandbox)
        _assert(r.returncode == 0, f"exit {r.returncode}: {r.stdout}{r.stderr}")

    tests.append(("marketplace add", _marketplace_add))

    def _marketplace_list() -> None:
        r = _run_claude(["plugin", "marketplace", "list"], sandbox)
        _assert(r.returncode == 0, f"exit {r.returncode}: {r.stdout}{r.stderr}")
        _assert(
            MARKETPLACE_NAME in r.stdout,
            f"'{MARKETPLACE_NAME}' not in marketplace list: {r.stdout}",
        )

    tests.append(("marketplace list", _marketplace_list))

    return tests


def _test_install(sandbox: Path) -> list[TestCase]:
    """Build plugin install + list test cases."""
    tests: list[TestCase] = []

    for plugin in PLUGINS:
        ref = f"{plugin}@{MARKETPLACE_NAME}"

        def _install(r_ref: str = ref, name: str = plugin) -> None:
            r = _run_claude(["plugin", "install", r_ref], sandbox)
            _assert(r.returncode == 0, f"install {name}: exit {r.returncode}: {r.stdout}{r.stderr}")

        tests.append((f"install: {plugin}", _install))

    def _plugin_list_all() -> None:
        r = _run_claude(["plugin", "list"], sandbox)
        _assert(r.returncode == 0, f"exit {r.returncode}: {r.stdout}{r.stderr}")
        for plugin in PLUGINS:
            _assert(plugin in r.stdout, f"'{plugin}' not in plugin list: {r.stdout}")

    tests.append((f"plugin list ({len(PLUGINS)} installed)", _plugin_list_all))

    return tests


def _test_disable_enable(sandbox: Path) -> list[TestCase]:
    """Build disable/enable cycle test cases for the first plugin."""
    tests: list[TestCase] = []
    target = PLUGINS[0]
    target_ref = f"{target}@{MARKETPLACE_NAME}"

    def _disable() -> None:
        r = _run_claude(["plugin", "disable", target_ref], sandbox)
        _assert(r.returncode == 0, f"disable: exit {r.returncode}: {r.stdout}{r.stderr}")
        r2 = _run_claude(["plugin", "list"], sandbox)
        _assert(r2.returncode == 0, f"list after disable: exit {r2.returncode}")
        _assert("disabled" in r2.stdout.lower(), f"Expected 'disabled' in list: {r2.stdout}")

    tests.append((f"disable: {target}", _disable))

    def _enable() -> None:
        r = _run_claude(["plugin", "enable", target_ref], sandbox)
        _assert(r.returncode == 0, f"enable: exit {r.returncode}: {r.stdout}{r.stderr}")
        r2 = _run_claude(["plugin", "list"], sandbox)
        _assert(r2.returncode == 0, f"list after enable: exit {r2.returncode}")
        _assert("enabled" in r2.stdout.lower(), f"Expected 'enabled' in list: {r2.stdout}")

    tests.append((f"enable: {target}", _enable))

    return tests


def _test_uninstall(sandbox: Path) -> list[TestCase]:
    """Build plugin uninstall + empty list test cases."""
    tests: list[TestCase] = []

    for plugin in PLUGINS:
        ref = f"{plugin}@{MARKETPLACE_NAME}"

        def _uninstall(r_ref: str = ref, name: str = plugin) -> None:
            r = _run_claude(["plugin", "uninstall", r_ref], sandbox)
            _assert(
                r.returncode == 0,
                f"uninstall {name}: exit {r.returncode}: {r.stdout}{r.stderr}",
            )

        tests.append((f"uninstall: {plugin}", _uninstall))

    def _plugin_list_empty() -> None:
        r = _run_claude(["plugin", "list"], sandbox)
        _assert(r.returncode == 0, f"exit {r.returncode}: {r.stdout}{r.stderr}")
        for plugin in PLUGINS:
            _assert(
                plugin not in r.stdout,
                f"'{plugin}' still in plugin list after uninstall: {r.stdout}",
            )

    tests.append(("plugin list (0 installed)", _plugin_list_empty))

    return tests


def _test_marketplace_remove(sandbox: Path) -> list[TestCase]:
    """Build marketplace remove + empty list test cases."""
    tests: list[TestCase] = []

    def _marketplace_remove() -> None:
        r = _run_claude(["plugin", "marketplace", "remove", MARKETPLACE_NAME], sandbox)
        _assert(r.returncode == 0, f"exit {r.returncode}: {r.stdout}{r.stderr}")

    tests.append(("marketplace remove", _marketplace_remove))

    def _marketplace_list_empty() -> None:
        r = _run_claude(["plugin", "marketplace", "list"], sandbox)
        _assert(r.returncode == 0, f"exit {r.returncode}: {r.stdout}{r.stderr}")
        _assert(
            MARKETPLACE_NAME not in r.stdout,
            f"'{MARKETPLACE_NAME}' still in marketplace list: {r.stdout}",
        )

    tests.append(("marketplace list (empty)", _marketplace_list_empty))

    return tests


# ---------------------------------------------------------------------------
# Suite runner
# ---------------------------------------------------------------------------


def _run_suite(source_type: t.Literal["local", "github"]) -> tuple[int, int]:
    """Run the full test suite for one source type.

    Returns
    -------
    tuple[int, int]
        (passed, total) counts.
    """
    if source_type == "local":
        source = str(REPO_ROOT)
        label = f"local ({PrivatePath(REPO_ROOT)})"
    else:
        source = GITHUB_SOURCE
        label = f"github ({GITHUB_SOURCE})"

    console.print(f"\n[bold]Source: {label}[/bold]")

    sandbox = Path(tempfile.mkdtemp(prefix="claude-e2e-"))
    try:
        tests: list[TestCase] = []
        tests.extend(_test_validate(sandbox))
        tests.extend(_test_marketplace_add(sandbox, source))
        tests.extend(_test_install(sandbox))
        tests.extend(_test_disable_enable(sandbox))
        tests.extend(_test_uninstall(sandbox))
        tests.extend(_test_marketplace_remove(sandbox))

        passed = sum(_run_test(name, fn) for name, fn in tests)
        total = len(tests)
        return passed, total
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


@app.command()
def main(
    source: t.Annotated[Source, typer.Option(help="Source type: local, github, or both")] = "local",
) -> None:
    """Run E2E plugin lifecycle tests against the Claude CLI."""
    if shutil.which("claude") is None:
        console.print("[red]Error:[/red] 'claude' CLI not found in PATH")
        raise SystemExit(1)

    console.print("[bold]E2E Plugin Lifecycle Tests[/bold]")
    console.print("=" * 40)

    sources: list[t.Literal["local", "github"]]
    if source == "both":
        sources = ["local", "github"]
    else:
        sources = [source]

    total_passed = 0
    total_tests = 0

    for src in sources:
        passed, total = _run_suite(src)
        total_passed += passed
        total_tests += total

    console.print()
    if total_passed == total_tests:
        console.print(f"[green bold]{total_passed}/{total_tests} tests passed[/green bold]")
    else:
        failed = total_tests - total_passed
        console.print(f"[red bold]{failed}/{total_tests} tests failed[/red bold]")
        raise SystemExit(1)


if __name__ == "__main__":
    app()
