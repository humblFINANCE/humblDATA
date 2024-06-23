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
    with open(path, "w") as f:
        f.write(textwrap.dedent(content))


def generate_context_files(project_root: Path, context: str) -> None:
    """
    Generate the __init__.py file for a given context.

    Parameters
    ----------
    project_root : Path
        The root directory of the project.
    context : str
        The name of the context.

    """
    file_path = (
        project_root
        / "src"
        / "humbldata"
        / "core"
        / "standard_models"
        / context
        / "__init__.py"
    )
    content = f'''
    """
    Context: {context.capitalize()}

    This module defines the standard models for the {context.capitalize()} context.
    """

    from pydantic import BaseModel, Field

    class {context.capitalize()}QueryParams(BaseModel):
        example_field: str = Field(..., description="An example field")

        @validator('example_field')
        def validate_example_field(cls, v):
            if len(v) < 3:
                raise ValueError("example_field must be at least 3 characters long")
            return v

    class {context.capitalize()}Data(BaseModel):
        result: str = Field(..., description="The result of the {context.capitalize()} operation")
    '''
    write_file(file_path, content)


def generate_command_files(
    project_root: Path, context: str, category: str, command: str
) -> None:
    """
    Generate the __init__.py file for a given command.

    Parameters
    ----------
    project_root : Path
        The root directory of the project.
    context : str
        The name of the context.
    category : str
        The name of the category.
    command : str
        The name of the command.

    """
    file_path = (
        project_root
        / "src"
        / "humbldata"
        / context
        / category
        / command
        / "__init__.py"
    )
    content = f'''
    """
    Context: {context.capitalize()} || Category: {category.capitalize()} || Command: {command.capitalize()}

    This module defines the {command} command.
    """

    from pydantic import BaseModel, Field

    class {command.capitalize()}QueryParams(BaseModel):
        example_field: str = Field(..., description="An example field")

        @validator('example_field')
        def validate_example_field(cls, v):
            if len(v) < 3:
                raise ValueError("example_field must be at least 3 characters long")
            return v

    class {command.capitalize()}Data(BaseModel):
        result: str = Field(..., description="The result of the {command.capitalize()} operation")
    '''
    write_file(file_path, content)


def generate_context_controller(project_root: Path, context: str) -> None:
    """
    Generate the controller file for a given context.

    Parameters
    ----------
    project_root : Path
        The root directory of the project.
    context : str
        The name of the context.

    """
    file_path = project_root / "src" / "humbldata" / context / "controller.py"
    content = f'''
    """
    Context: {context.capitalize()}

    This module defines the controller for the {context.capitalize()} context.
    """

    def handle_request(query_params):
        """
        Handle a request for the {context.capitalize()} context.

        Parameters
        ----------
        query_params : {context.capitalize()}QueryParams
            The query parameters for the request.

        Returns
        -------
        {context.capitalize()}Data
            The result of the request.
        """
        return {context.capitalize()}Data(result="Success")
    '''
    write_file(file_path, content)


def generate_category_controller(
    project_root: Path, context: str, category: str
) -> None:
    """
    Generate the controller file for a given category.

    Parameters
    ----------
    project_root : Path
        The root directory of the project.
    context : str
        The name of the context.
    category : str
        The name of the category.

    """
    file_path = (
        project_root
        / "src"
        / "humbldata"
        / context
        / category
        / "controller.py"
    )
    content = f'''
    """
    Context: {context.capitalize()} || Category: {category.capitalize()}

    This module defines the controller for the {category.capitalize()} category.
    """

    def handle_request(query_params):
        """
        Handle a request for the {category.capitalize()} category.

        Parameters
        ----------
        query_params : {category.capitalize()}QueryParams
            The query parameters for the request.

        Returns
        -------
        {category.capitalize()}Data
            The result of the request.
        """
        return {category.capitalize()}Data(result="Success")
    '''
    write_file(file_path, content)


def generate_model(
    project_root: Path, context: str, category: str, command: str
) -> None:
    """
    Generate the model file for a given command.

    Parameters
    ----------
    project_root : Path
        The root directory of the project.
    context : str
        The name of the context.
    category : str
        The name of the category.
    command : str
        The name of the command.

    """
    file_path = (
        project_root
        / "src"
        / "humbldata"
        / context
        / category
        / command
        / "model.py"
    )
    content = f'''
    """
    Context: {context.capitalize()} || Category: {category.capitalize()} || Command: {command.capitalize()}

    This module defines the model for the {command.capitalize()} command.
    """

    def dummy_function():
        """
        A dummy function for the {command} command.

        This is a placeholder function to serve as an example.
        """
        return "Dummy function result"
    '''
    write_file(file_path, content)


def generate_view(
    project_root: Path, context: str, category: str, command: str
) -> None:
    """
    Generate the view file for a given command.

    Parameters
    ----------
    project_root : Path
        The root directory of the project.
    context : str
        The name of the context.
    category : str
        The name of the category.
    command : str
        The name of the command.

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
    Context: {context.capitalize()} || Category: {category.capitalize()} || Command: {command.capitalize()}

    This module defines the view for the {command.capitalize()} command.
    """

    def render_view():
        """
        Render the view for the {command} command.

        This is a dummy function to serve as an example.
        """
        return "View rendered"
    '''
    write_file(file_path, content)


def generate_helpers(
    project_root: Path, context: str, category: str, command: str
) -> None:
    """
    Generate the helpers file for a given command.

    Parameters
    ----------
    project_root : Path
        The root directory of the project.
    context : str
        The name of the context.
    category : str
        The name of the category.
    command : str
        The name of the command.

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
    Context: {context.capitalize()} || Category: {category.capitalize()} || Command: {command.capitalize()}

    Helper functions for the {command} command.
    """

    def helper_function():
        """
        A helper function for the {command} command.

        This is a dummy function to serve as an example.
        """
        return "Helper function result"
    '''
    write_file(file_path, content)


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
    generate_context_controller(project_root, context)

    # Generate category controllers for each level
    current_category = ""
    for cat in categories:
        current_category = (
            f"{current_category}/{cat}" if current_category else cat
        )
        generate_category_controller(project_root, context, current_category)

    generate_model(project_root, context, category, command)

    if add_view:
        generate_view(project_root, context, category, command)
    if add_helpers:
        generate_helpers(project_root, context, category, command)

    print("Files generated successfully!")


if __name__ == "__main__":
    main()
