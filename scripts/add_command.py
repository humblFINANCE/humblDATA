"""Create boilerplate for humbldata contexts, categories, and commands."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


def get_project_root() -> Path:
    """Return the project root containing ``src/humbldata``."""
    current_path = Path.cwd()
    while current_path != current_path.parent:
        if (current_path / "src" / "humbldata").exists():
            return current_path
        current_path = current_path.parent
    msg = "Could not find project root containing src/humbldata"
    raise FileNotFoundError(msg)


def clean_name(name: str, case: str = "snake_case") -> str:
    """
    Normalize a human-facing name into a Python identifier style.

    Parameters
    ----------
    name : str
        The raw name supplied by a user.
    case : str
        One of ``snake_case``, ``camelCase``, or ``PascalCase``.
    """
    words = re.findall(r"[A-Za-z0-9]+", name)
    if not words:
        msg = f"Invalid empty name: {name!r}"
        raise ValueError(msg)

    if case.lower() == "snake_case":
        return "_".join(word.lower() for word in words)
    if case.lower() == "camelcase":
        first, *rest = words
        return first.lower() + "".join(word.capitalize() for word in rest)
    if case.lower() == "pascalcase":
        return "".join(word.capitalize() for word in words)
    msg = "Invalid case. Must be 'snake_case', 'camelCase', or 'PascalCase'."
    raise ValueError(msg)


def category_parts(category: str) -> list[str]:
    """Return normalized category path parts."""
    return [clean_name(part) for part in category.split("/") if part.strip()]


def category_name(category: str) -> str:
    """Return the normalized slash-separated category path."""
    parts = category_parts(category)
    if not parts:
        msg = "Category is required"
        raise ValueError(msg)
    return "/".join(parts)


def class_name(*names: str) -> str:
    """Return a PascalCase class name from one or more names."""
    return "".join(clean_name(name, case="PascalCase") for name in names)


def write_file_if_missing(path: Path, content: str) -> None:
    """Write a new text file without overwriting existing user code."""
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n")


def ensure_init(path: Path) -> None:
    """Ensure a Python package initializer exists."""
    write_file_if_missing(path / "__init__.py", '"""Generated package."""\n')


def write_init_model_if_missing(path: Path, content: str) -> None:
    """Write a package model, replacing only the generated placeholder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() != '"""Generated package."""\n':
        return
    path.write_text(content.strip() + "\n")


def package_path(project_root: Path, *parts: str) -> Path:
    """Return a path under ``src/humbldata``."""
    return project_root / "src" / "humbldata" / Path(*parts)


def standard_model_path(project_root: Path, *parts: str) -> Path:
    """Return a path under ``src/humbldata/core/standard_models``."""
    return package_path(project_root, "core", "standard_models", *parts)


def create_context(project_root: Path, context: str) -> None:
    """Create a top-level context package and standard model."""
    context = clean_name(context)
    context_class = class_name(context)
    context_package = package_path(project_root, context)
    ensure_init(context_package)

    write_file_if_missing(
        context_package / f"{context}_controller.py",
        f'''
"""{context_class} context controller."""

from humbldata.core.standard_models.{context} import {context_class}QueryParams


class {context_class}({context_class}QueryParams):
    """Top-level controller for the {context} context."""

    def __init__(self, *args, **kwargs):
        """Initialize the {context_class} controller."""
        super().__init__(*args, **kwargs)
''',
    )

    model_package = standard_model_path(project_root, context)
    write_init_model_if_missing(
        model_package / "__init__.py",
        f'''
"""{context_class} context standard models."""

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.query_params import QueryParams


class {context_class}QueryParams(QueryParams):
    """Query parameters for the {context} context."""

    pass


class {context_class}Data(Data):
    """Data model for the {context} context."""

    pass
''',
    )


def update_context_controller(
    project_root: Path, context: str, category: str
) -> None:
    """Expose a category from an existing context controller."""
    context = clean_name(context)
    category = category_name(category)
    category_attr = clean_name(category.split("/")[-1])
    category_class = class_name(category_attr)
    controller_path = package_path(
        project_root, context, f"{context}_controller.py"
    )
    if not controller_path.exists():
        create_context(project_root, context)

    content = controller_path.read_text()
    import_line = (
        f"from humbldata.{context}.{category.replace('/', '.')}"
        f".{category_attr}_controller import {category_class}"
    )
    if import_line not in content:
        lines = content.splitlines()
        insert_at = 0
        for index, line in enumerate(lines):
            if line.startswith(("from ", "import ")):
                insert_at = index + 1
        lines.insert(insert_at, import_line)
        content = "\n".join(lines) + "\n"

    method_signature = f"    def {category_attr}(self):"
    if method_signature not in content:
        content = (
            content.rstrip()
            + f'''

    @property
    def {category_attr}(self):
        """Return the {category_attr} category controller."""
        return {category_class}(context_params=self)
'''
        )
    controller_path.write_text(content)


def create_category(project_root: Path, context: str, category: str) -> None:
    """Create a category package under an existing or new context."""
    context = clean_name(context)
    category = category_name(category)
    category_attr = clean_name(category.split("/")[-1])
    category_class = class_name(category_attr)
    context_class = class_name(context)

    create_context(project_root, context)

    category_package = package_path(project_root, context, *category.split("/"))
    ensure_init(category_package)
    write_file_if_missing(
        category_package / f"{category_attr}_controller.py",
        f'''
"""{context_class} {category_class} category controller."""

from humbldata.core.standard_models.{context} import {context_class}QueryParams
from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.core.utils.logger import setup_logger

logger = setup_logger(__name__)


class {category_class}:
    """Controller for commands in the {category} category."""

    def __init__(self, context_params: {context_class}QueryParams):
        """Store inherited context parameters."""
        self.context_params = context_params
''',
    )
    ensure_init(
        standard_model_path(project_root, context, *category.split("/"))
    )
    update_context_controller(project_root, context, category)


def update_category_controller(
    project_root: Path, context: str, category: str, command: str
) -> None:
    """Expose a command from a category controller."""
    context = clean_name(context)
    category = category_name(category)
    command = clean_name(command)
    category_attr = clean_name(category.split("/")[-1])
    command_class = class_name(command)
    controller_path = package_path(
        project_root,
        context,
        *category.split("/"),
        f"{category_attr}_controller.py",
    )
    if not controller_path.exists():
        create_category(project_root, context, category)

    content = controller_path.read_text()
    import_line = (
        f"from humbldata.core.standard_models.{context}."
        f"{category.replace('/', '.')}.{command} import "
        f"{command_class}Fetcher, {command_class}QueryParams"
    )
    if import_line not in content:
        lines = content.splitlines()
        insert_at = 0
        for index, line in enumerate(lines):
            if line.startswith(("from ", "import ")):
                insert_at = index + 1
        lines.insert(insert_at, import_line)
        content = "\n".join(lines) + "\n"

    method_signature = f"    def {command}(self, **kwargs:"
    if method_signature not in content:
        content = (
            content.rstrip()
            + f'''

    def {command}(self, **kwargs: {command_class}QueryParams):
        """Execute the {command} command."""
        try:
            fetcher = {command_class}Fetcher(
                context_params=self.context_params,
                command_params=kwargs,
            )
            return fetcher.fetch_data()
        except Exception as exc:
            logger.exception("Error calculating {command}")
            raise HumblDataError(
                f"Failed to calculate {command}: {{exc!s}}"
            ) from exc
'''
        )
    controller_path.write_text(content)


def create_command(  # noqa: PLR0913
    project_root: Path,
    context: str,
    category: str,
    command: str,
    *,
    add_helpers: bool = False,
    add_view: bool = False,
) -> None:
    """Create command logic and standard model boilerplate."""
    context = clean_name(context)
    category = category_name(category)
    command = clean_name(command)
    command_class = class_name(command)
    context_class = class_name(context)

    create_category(project_root, context, category)

    command_package = package_path(
        project_root, context, *category.split("/"), command
    )
    ensure_init(command_package)
    write_file_if_missing(
        command_package / "model.py",
        f'''
"""{command_class} command logic."""


def {command}():
    """Execute the {command} command."""
    pass
''',
    )
    if add_helpers:
        write_file_if_missing(
            command_package / "helpers.py",
            f'''
"""{command_class} command helpers."""


def helper_function():
    """Return a placeholder helper result."""
    return "Helper function result"
''',
        )
    if add_view:
        write_file_if_missing(
            command_package / "view.py",
            f'''
"""{command_class} command views."""

import polars as pl


def generate_plots(data: pl.LazyFrame):
    """Generate plots for {command} data."""
    return []
''',
        )

    standard_model = standard_model_path(
        project_root, context, *category.split("/"), f"{command}.py"
    )
    write_file_if_missing(
        standard_model,
        f'''
"""{command_class} standard model."""

from typing import TypeVar

import polars as pl

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.{context} import {context_class}QueryParams
from humbldata.core.utils.env import Env
from humbldata.core.utils.logger import log_start_end, setup_logger

env = Env()
Q = TypeVar("Q", bound={context_class}QueryParams)
logger = setup_logger("{command_class}Fetcher", level=env.LOGGER_LEVEL)


class {command_class}QueryParams(QueryParams):
    """Query parameters for the {command} command."""

    pass


class {command_class}Data(Data):
    """Data model for the {command} command."""

    pass


class {command_class}Fetcher:
    """Fetcher for the {command} command."""

    def __init__(
        self,
        context_params: {context_class}QueryParams,
        command_params: {command_class}QueryParams | dict | None = None,
    ):
        """Initialize the fetcher with context and command parameters."""
        self.context_params = context_params
        self.command_params = command_params
        self.warnings = []
        self.extra = {{}}
        self.chart = None

    def transform_query(self):
        """Normalize command query parameters."""
        if self.command_params is None:
            self.command_params = {command_class}QueryParams()
        elif isinstance(self.command_params, dict):
            self.command_params = {command_class}QueryParams(
                **self.command_params
            )
        return self

    def extract_data(self):
        """Extract raw data for the command."""
        self.data = pl.DataFrame()
        return self

    def transform_data(self):
        """Transform raw data for the command."""
        self.transformed_data = self.data
        return self

    @log_start_end(logger=logger)
    def fetch_data(self):
        """Execute the transform, extract, transform pattern."""
        self.transform_query()
        self.extract_data()
        self.transform_data()

        context_warnings = getattr(self.context_params, "warnings", [])
        return HumblObject(
            results=self.transformed_data,
            provider=getattr(self.context_params, "provider", None),
            warnings=context_warnings + self.warnings,
            chart=self.chart,
            context_params=self.context_params,
            command_params=self.command_params,
            extra=self.extra,
        )
''',
    )
    update_category_controller(project_root, context, category, command)


def prompt_missing(value: str | None, label: str) -> str:
    """Prompt only when a CLI argument was omitted."""
    if value:
        return value
    return input(f"Enter the {label}: ")


def build_parser() -> argparse.ArgumentParser:
    """Build the ``poe create`` command parser."""
    parser = argparse.ArgumentParser(
        prog="poe create",
        description="Create humbldata boilerplate.",
    )
    subparsers = parser.add_subparsers(dest="kind")

    context_parser = subparsers.add_parser(
        "context", help="Create a new top-level context module"
    )
    context_parser.add_argument("context", nargs="?")

    category_parser = subparsers.add_parser(
        "category", help="Create a category module within a context"
    )
    category_parser.add_argument("context", nargs="?")
    category_parser.add_argument("category", nargs="?")

    command_parser = subparsers.add_parser(
        "command", help="Create a command module within a category"
    )
    command_parser.add_argument("context", nargs="?")
    command_parser.add_argument("category", nargs="?")
    command_parser.add_argument("command", nargs="?")
    command_parser.add_argument(
        "--helpers",
        action="store_true",
        help="Also create a helpers.py boilerplate file",
    )
    command_parser.add_argument(
        "--view",
        action="store_true",
        help="Also create a view.py boilerplate file",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Run the boilerplate generator CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    project_root = get_project_root()

    if args.kind == "context":
        create_context(project_root, prompt_missing(args.context, "context"))
    elif args.kind == "category":
        create_category(
            project_root,
            prompt_missing(args.context, "context"),
            prompt_missing(args.category, "category"),
        )
    elif args.kind == "command":
        create_command(
            project_root,
            prompt_missing(args.context, "context"),
            prompt_missing(args.category, "category"),
            prompt_missing(args.command, "command"),
            add_helpers=args.helpers,
            add_view=args.view,
        )
    else:
        parser.print_help()
        raise SystemExit(2)

    sys.stdout.write("Files generated successfully!\n")


if __name__ == "__main__":
    main(sys.argv[1:])
