"""Nox sessions for the CI test matrix."""

from __future__ import annotations

from pathlib import Path

import nox

PYTHON_VERSIONS = ("3.9", "3.10", "3.11")
SMOKE_TESTS = ("tests/test_import.py", "tests/test_cli.py")
PYTEST_DEPS = ("pytest>=8.3.5", "pytest-emoji>=0.2.0", "pytest-md>=0.2.0")

nox.options.sessions = ["tests"]


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the stable pytest smoke suite."""
    session.install("-e", ".")
    session.install(*PYTEST_DEPS)

    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)

    pytest_args = [*SMOKE_TESTS, *session.posargs]
    session.run(
        "pytest",
        *pytest_args,
        env={"PYTHONPATH": "src"},
    )
