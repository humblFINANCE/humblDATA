"""Nox sessions for humblDATA testing suite.

Runs pytest across a matrix of supported Python versions with
coverage and JUnit XML reporting for CI integration.
"""

from __future__ import annotations

import nox

# Supported Python versions (aligned with requires-python >=3.11,<3.13)
PYTHON_VERSIONS = ["3.11", "3.12"]

# Default locations
PYTEST_LOCATIONS = ["src", "tests"]


@nox.session(python=PYTHON_VERSIONS, tags=["tests"])
def tests(session: nox.Session) -> None:
    """Run the full test suite with coverage."""
    session.install(".[test]")
    session.install(
        "coverage[toml]",
        "pytest",
        "pytest-asyncio",
        "pytest-mock",
        "pytest-xdist",
        "pytest-clarity",
    )
    session.run(
        "coverage",
        "run",
        "--module",
        "pytest",
        *PYTEST_LOCATIONS,
        "--color=yes",
        "--exitfirst",
        "--failed-first",
        "--strict-config",
        "--strict-markers",
        "--verbosity=2",
        "--junitxml=reports/pytest.xml",
    )
    session.run("coverage", "report")
    session.run("coverage", "xml", "-o", "reports/coverage.xml")


@nox.session(python=PYTHON_VERSIONS[0], tags=["lint"])
def lint(session: nox.Session) -> None:
    """Run linting checks."""
    session.install("ruff")
    session.run("ruff", "check", "src", "tests")


@nox.session(python=PYTHON_VERSIONS[0], tags=["tests"])
def unit(session: nox.Session) -> None:
    """Run only unit tests."""
    session.install(".[test]")
    session.install("pytest", "pytest-asyncio", "pytest-mock")
    session.run(
        "pytest",
        "tests/unittests",
        "--color=yes",
        "--verbosity=2",
        "-m",
        "not slow",
    )


@nox.session(python=PYTHON_VERSIONS[0], tags=["tests"])
def integration(session: nox.Session) -> None:
    """Run only integration tests."""
    session.install(".[test]")
    session.install("pytest", "pytest-asyncio", "pytest-mock")
    session.run(
        "pytest",
        "tests/integration",
        "--color=yes",
        "--verbosity=2",
        "-m",
        "not slow",
    )
