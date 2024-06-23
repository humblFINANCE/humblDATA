import os
from pathlib import Path
import textwrap
from typing import Tuple, List


def prompt_user() -> Tuple[str, str, str, bool, bool]:
    """
    Prompt the user for input to create a new command.

    Returns
    -------
    Tuple[str, str, str, bool, bool]
        A tuple containing:
        - context: The context name (lowercase)
        - category: The category name (lowercase)
        - command: The command name (lowercase)
        - add_view: Boolean indicating whether to add a view.py file
        - add_helpers: Boolean indicating whether to add a helpers.py file

    """
    context = input("Enter the context name: ").lower()
    category = input(
        "Enter the category name (use '/' for sub-categories): "
    ).lower()
    command = input("Enter the command name: ").lower()
    add_view = (
        input("Do you want to add a view.py file? (y/n): ").lower() == "y"
    )
    add_helpers = (
        input("Do you want to add a helpers.py file? (y/n): ").lower() == "y"
    )
    return context, category, command, add_view, add_helpers


def get_project_root() -> Path:
    current_path = Path.cwd()
    while current_path != current_path.parent:
        if (current_path / "src" / "humbldata").exists():
            return current_path
        current_path = current_path.parent
    raise FileNotFoundError(
        "Could not find project root containing src/humbldata"
    )


def create_directory(path: Path) -> None:
    """
    Create a directory and its parent directories if they don't exist.

    Parameters
    ----------
    path : Path
        The path of the directory to create.

    """
    path.mkdir(parents=True, exist_ok=True)


def write_file(path: Path, content: str) -> None:
    """
    Write content to a file, creating the file if it doesn't exist.

    Parameters
    ----------
    path : Path
        The path of the file to write.
    content : str
        The content to write to the file.

    """
    with path.open("w") as file:
        file.write(content)


def clean_name(name: str) -> str:
    """
    Clean and format a name to follow CamelCase convention.

    Parameters
    ----------
    name : str
        The name to clean and format.

    Returns
    -------
    str
        The cleaned and formatted name.
    """
    return "".join(word.capitalize() for word in name.split("_"))


def generate_context_files(project_root: Path, context: str) -> None:
    """
    Generate the context files.

    Parameters
    ----------
    project_root : Path
        The root path of the project.
    context : str
        The context name.
    """
    file_path = project_root / "src" / "humbldata" / context / "__init__.py"
    content = f'''
"""
**Context: {clean_name(context)}**.

A category to group in the `{clean_name(context)}()`

"""

'''
    write_file(file_path, content)

    # Create __init__.py in the context directory
    init_file_path = file_path.parent / "__init__.py"
    write_file(init_file_path, "")


def generate_command_files(
    project_root: Path, context: str, category: str, command: str
) -> None:
    """
    Generate the command files.

    Parameters
    ----------
    project_root : Path
        The root path of the project.
    context : str
        The context name.
    category : str
        The category name.
    command : str
        The command name.
    """
    file_path = (
        project_root
        / "src"
        / "humbldata"
        / context
        / category
        / command
        / f"{command}.py"
    )
    content = f'''
"""
**Context: {clean_name(context)} || Category: {clean_name(category)} || Command: {clean_name(command)}**.

The {clean_name(command)} Command Module.
"""

from pydantic import BaseModel, Field, field_validator

class {clean_name(command)}QueryParams(BaseModel):
    example_field: str = Field(..., description="An example field")

    @field_validator('example_field')
    def validate_example_field(cls, v):
        if len(v) < 3:
            raise ValueError("example_field must be at least 3 characters long")
        return v

class {clean_name(command)}Data(BaseModel):
    result: str = Field(..., description="The result of the {clean_name(command)} operation")
'''
    write_file(file_path, content)

    # Create __init__.py in the category directory
    init_file_path = file_path.parent / "__init__.py"
    write_file(init_file_path, "")


def generate_context_controller(
    project_root: Path, context: str, category: str
) -> None:
    """
    Generate the context controller file.

    Parameters
    ----------
    project_root : Path
        The root path of the project.
    context : str
        The context name.
    category : str
        The category name.
    """
    file_path = (
        project_root
        / "src"
        / "humbldata"
        / context
        / f"{context}_controller.py"
    )
    content = f'''
"""
**Context: {clean_name(context)}**.

The {clean_name(context)} Controller Module.
"""

from humbldata.core.standard_models.{context} import {clean_name(context)}QueryParams

class {clean_name(context)}({clean_name(context)}QueryParams):
    """
    A top-level {clean_name(category)} controller for data analysis tools in `humblDATA`.

    This module serves as the primary controller, routing user-specified
    {clean_name(context)}QueryParams as core arguments that are used to fetch time series
    data.

    The `{clean_name(context)}` controller also gives access to all sub-modules and their
    functions.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the {clean_name(context)} module.

        This method does not take any parameters and does not return anything.
        """
        super().__init__(*args, **kwargs)

    @property
    def {clean_name(category).lower()}(self):
        """
        The {clean_name(category)} submodule of the {clean_name(context)} controller.

        Access to all the {clean_name(category)} indicators. When the {clean_name(context)} class is
        instantiated the parameters are initialized with the {clean_name(context)}QueryParams
        class, which hold all the fields needed for the context_params, like the
        symbol, interval, start_date, and end_date.
        """
        return {clean_name(category)}(context_params=self)
'''
    write_file(file_path, content.strip())

    # Create __init__.py in the context directory
    init_file_path = file_path.parent / "__init__.py"
    write_file(init_file_path, "")


def generate_category_controller(
    project_root: Path, context: str, category: str, command: str
) -> None:
    """
    Generate the category controller file.

    Parameters
    ----------
    project_root : Path
        The root path of the project.
    context : str
        The context name.
    category : str
        The category name.
    command : str
        The command name.
    """
    file_path = (
        project_root
        / "src"
        / "humbldata"
        / context
        / category
        / f"{category}_controller.py"
    )
    content = f'''
"""
**Context: {clean_name(context)} || Category: {clean_name(category)}**.

The {clean_name(category)} Controller Module.
"""

from humbldata.core.standard_models.{context} import {clean_name(context)}QueryParams
from humbldata.core.standard_models.{context}.{category}.{command} import (
    {clean_name(command)}QueryParams,
)


class {clean_name(category)}QueryParams):
    """
    A {clean_name(category)} controller for data analysis tools in `humblDATA`.

    This module serves as the primary controller, routing user-specified
    {clean_name(command)}QueryParams as core arguments that are used to fetch time series
    data.

    The `{clean_name(category)}` controller also gives access to all sub-modules and their
    functions.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the {clean_name(category)} module.

        This method does not take any parameters and does not return anything.
        """
        super().__init__(*args, **kwargs)

    @property
    def {clean_name(command).lower()}(self):
        """
        The {clean_name(command)} submodule of the {clean_name(category)} controller.

        Access to all the {clean_name(command)} indicators. When the {clean_name(category)} class is
        instantiated the parameters are initialized with the {clean_name(command)}QueryParams
        class, which hold all the fields needed for the context_params, like the
        symbol, interval, start_date, and end_date.
        """
        return {clean_name(command)}(context_params=self)
'''
    write_file(file_path, content.strip())

    # Create __init__.py in the category directory
    init_file_path = file_path.parent / "__init__.py"
    write_file(init_file_path, "")


def generate_standard_model(
    project_root: Path, context: str, category: str, command: str
) -> None:
    """
    Generate the model file.

    Parameters
    ----------
    project_root : Path
        The root path of the project.
    context : str
        The context name.
    category : str
        The category name.
    command : str
        The command name.
    """
    file_path = (
        project_root
        / "src"
        / "humbldata"
        / "core"
        / "standard_models"
        / context
        / category
        / f"{command}.py"
    )
    content = f'''
"""
{clean_name(command)} Standard Model.

Context: {clean_name(context)} || Category: {clean_name(category)} || Command: {clean_name(command)}.

This module is used to define the QueryParams and Data model for the
{clean_name(command)} command.
"""

from typing import Literal

from pydantic import Field, field_validator

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.query_params import QueryParams

{clean_name(command).upper()}_QUERY_DESCRIPTIONS = {{
    "example_field1": "Description for example field 1",
    "example_field2": "Description for example field 2",
}}


class {clean_name(command)}QueryParams(QueryParams):
    """
    QueryParams model for the {clean_name(command)} command, a Pydantic v2 model.

    Parameters
    ----------
    example_field1 : str
        An example field.
    example_field2 : bool
        Another example field.
    """

    example_field1: str = Field(
        default="default_value",
        title="Example Field 1",
        description={clean_name(command).upper()}_QUERY_DESCRIPTIONS.get("example_field1", ""),
    )
    example_field2: bool = Field(
        default=True,
        title="Example Field 2",
        description={clean_name(command).upper()}_QUERY_DESCRIPTIONS.get("example_field2", ""),
    )

    @field_validator("example_field1", mode="after")
    @classmethod
    def validate_example_field1(cls, v: str) -> str:
        # Add any validation logic here
        return v


class {clean_name(command)}Data(Data):
    """
    Data model for the {clean_name(command)} command, a Pandera.Polars Model.

    Parameters
    ----------
    # Add your data model parameters here
    """

    # Add your data model fields here
'''
    write_file(file_path, content)

    # Create __init__.py in the category directory
    init_file_path = file_path.parent / "__init__.py"
    write_file(init_file_path, "")


def generate_view(
    project_root: Path, context: str, category: str, command: str
) -> None:
    """
    Generate the view file.

    Parameters
    ----------
    project_root : Path
        The root path of the project.
    context : str
        The context name.
    category : str
        The category name.
    command : str
        The command name.
    """
    file_path = (
        project_root
        / "src"
        / "humbldata"
        / context
        / category
        / command
        / "view.py"
    )
    content = f'''
"""
**Context: {clean_name(context)} || Category: {clean_name(category)} || Command: {clean_name(command)}**.

The {clean_name(command)} View Module.
"""

def render_view(data):
    return f"Rendering view for {{data}}"
'''
    write_file(file_path, content)

    # Create __init__.py in the category directory
    init_file_path = file_path.parent / "__init__.py"
    write_file(init_file_path, "")


def generate_helpers(
    project_root: Path, context: str, category: str, command: str
) -> None:
    """
    Generate the helpers file.

    Parameters
    ----------
    project_root : Path
        The root path of the project.
    context : str
        The context name.
    category : str
        The category name.
    command : str
        The command name.
    """
    file_path = (
        project_root
        / "src"
        / "humbldata"
        / context
        / category
        / command
        / "helpers.py"
    )
    content = f'''
"""
**Context: {clean_name(context)} || Category: {clean_name(category)} || Command: {clean_name(command)}**.

The {clean_name(command)} Helpers Module.
"""

def helper_function():
    return "Helper function result"
'''
    write_file(file_path, content)

    # Create __init__.py in the category directory
    init_file_path = file_path.parent / "__init__.py"
    write_file(init_file_path, "")


def main() -> None:
    """
    Main function to orchestrate the creation of new command files and directories.
    """
    project_root = get_project_root()
    context, category, command, add_view, add_helpers = prompt_user()

    # Split category into sub-categories
    categories = category.split("/")

    # Create directories
    create_directory(
        project_root
        / "src"
        / "humbldata"
        / "core"
        / "standard_models"
        / context
    )
    current_path = (
        project_root
        / "src"
        / "humbldata"
        / "core"
        / "standard_models"
        / context
    )
    for cat in categories:
        current_path = current_path / cat
        create_directory(current_path)

    create_directory(project_root / "src" / "humbldata" / context)
    current_path = project_root / "src" / "humbldata" / context
    for cat in categories:
        current_path = current_path / cat
        create_directory(current_path)
    create_directory(current_path / command)

    # Generate files
    generate_context_files(project_root, context)
    generate_command_files(project_root, context, category, command)
    generate_context_controller(project_root, context, category)

    # Generate category controllers for each level
    current_category = ""
    for cat in categories:
        current_category = (
            f"{current_category}/{cat}" if current_category else cat
        )
        generate_category_controller(
            project_root, context, current_category, command
        )

    generate_standard_model(project_root, context, category, command)

    if add_view:
        generate_view(project_root, context, category, command)
    if add_helpers:
        generate_helpers(project_root, context, category, command)

    print("Files generated successfully!")


if __name__ == "__main__":
    main()
