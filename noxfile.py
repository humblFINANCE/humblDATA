"""Nox sessions for the GitHub Actions test matrix."""

import nox


PYTHON_VERSIONS = ("3.9", "3.10", "3.11")
SMOKE_TESTS = ("tests/test_import.py", "tests/test_cli.py")


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the stable smoke tests used by CI."""
    session.install("-e", ".")
    session.install("pytest", "pytest-md", "pytest-emoji")
    session.run("pytest", *SMOKE_TESTS, *session.posargs)
