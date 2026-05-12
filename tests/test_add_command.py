"""Tests for the poe create boilerplate generator."""

from __future__ import annotations

import tomllib
from pathlib import Path
from py_compile import compile as compile_python

from scripts.add_command import main


def make_project(tmp_path: Path) -> Path:
    """Create the minimum project layout the generator expects."""
    project_root = tmp_path / "project"
    (project_root / "src" / "humbldata").mkdir(parents=True)
    (project_root / "src" / "humbldata" / "__init__.py").write_text("")
    return project_root


def test_create_context_creates_context_and_standard_model(
    tmp_path: Path, monkeypatch
) -> None:
    """`create context` creates only the top-level context boilerplate."""
    project_root = make_project(tmp_path)
    monkeypatch.chdir(project_root)

    main(["context", "market-data"])

    context_package = project_root / "src" / "humbldata" / "market_data"
    standard_model = (
        project_root
        / "src"
        / "humbldata"
        / "core"
        / "standard_models"
        / "market_data"
        / "__init__.py"
    )

    assert (context_package / "__init__.py").exists()
    assert (context_package / "market_data_controller.py").exists()
    assert standard_model.exists()
    assert "class MarketDataQueryParams" in standard_model.read_text()


def test_create_command_creates_command_and_core_standard_model(
    tmp_path: Path, monkeypatch
) -> None:
    """`create command` creates command, helpers/view, and core models."""
    project_root = make_project(tmp_path)
    monkeypatch.chdir(project_root)

    main(
        [
            "command",
            "toolbox",
            "technical",
            "alpha-signal",
            "--helpers",
            "--view",
        ]
    )

    command_package = (
        project_root
        / "src"
        / "humbldata"
        / "toolbox"
        / "technical"
        / "alpha_signal"
    )
    command_model = command_package / "model.py"
    core_model = (
        project_root
        / "src"
        / "humbldata"
        / "core"
        / "standard_models"
        / "toolbox"
        / "technical"
        / "alpha_signal.py"
    )

    assert command_model.exists()
    assert "def alpha_signal()" in command_model.read_text()
    assert (command_package / "helpers.py").exists()
    assert (command_package / "view.py").exists()
    assert core_model.exists()

    core_model_text = core_model.read_text()
    assert "class AlphaSignalQueryParams" in core_model_text
    assert "class AlphaSignalData" in core_model_text
    assert "class AlphaSignalFetcher" in core_model_text

    for path in [
        command_model,
        command_package / "helpers.py",
        command_package / "view.py",
        core_model,
    ]:
        compile_python(str(path), doraise=True)


def test_poe_create_task_is_registered() -> None:
    """Pyproject exposes `poe create` as the public generator task."""
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())

    create_task = pyproject["tool"]["poe"]["tasks"]["create"]
    assert create_task["script"] == "scripts.add_command:main"
