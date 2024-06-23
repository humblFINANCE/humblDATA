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


def create_directory(path: Path) -> None:
    """
    Create a directory and its parent directories if they don't exist.

    Parameters
    ----------
    path : Path
        The path of the directory to create.

    """
    Path(path).mkdir(parents=True, exist_ok=True)


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


def generate_context_files(context: str) -> None:
    """
    Generate the __init__.py file for a given context.

    Parameters
    ----------
    context : str
        The name of the context.

    """
    file_path = Path(f"humbldata/core/standard_models/{context}/__init__.py")
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


def generate_command_files(context: str, category: str, command: str) -> None:
    """
    Generate the command file for a given context, category, and command.

    Parameters
    ----------
    context : str
        The name of the context.
    category : str
        The name of the category.
    command : str
        The name of the command.

    """
    file_path = Path(
        f"humbldata/core/standard_models/{context}/{category}/{command}.py"
    )
    content = f'''
    """
    Context: {context.capitalize()} || Category: {category.capitalize()} || Command: {command.capitalize()}

    This module defines the standard models for the {command.capitalize()} command.
    """

    from pydantic import BaseModel, Field

    class {command.capitalize()}QueryParams(BaseModel):
        example_param: str = Field(..., description="An example parameter for {command}")

        @validator('example_param')
        def validate_example_param(cls, v):
            if not v.isalpha():
                raise ValueError("example_param must contain only alphabetic characters")
            return v

    class {command.capitalize()}Data(BaseModel):
        result: str = Field(..., description="The result of the {command} operation")
    '''
    write_file(file_path, content)


def generate_context_controller(context: str) -> None:
    """
    Generate the context controller file for a given context.

    Parameters
    ----------
    context : str
        The name of the context.

    """
    file_path = Path(f"humbldata/{context}/{context}_controller.py")
    content = f'''
    """
    Context: {context.capitalize()}

    The {context.capitalize()} Controller Module.
    """

    from humbldata.core.standard_models.{context} import {context.capitalize()}QueryParams

    class {context.capitalize()}({context.capitalize()}QueryParams):
        """
        A top-level <context> controller for {context} in `humblDATA`.

        This module serves as the primary controller for the {context} context.
        """

        def __init__(self, *args, **kwargs):
            """
            Initialize the {context.capitalize()} module.
            """
            super().__init__(*args, **kwargs)

        # Add more methods as needed
    '''
    write_file(file_path, content)


def generate_category_controller(context: str, category: str) -> None:
    """
    Generate the category controller file for a given context and category.

    Parameters
    ----------
    context : str
        The name of the context.
    category : str
        The name of the category.

    """
    file_path = Path(f"humbldata/{context}/{category}/{category}_controller.py")
    content = f'''
    """
    Context: {context.capitalize()} || Category: {category.capitalize()}

    A controller to manage and compile all of the {category} models available.
    """

    from humbldata.core.standard_models.{context} import {context.capitalize()}QueryParams

    class {category.capitalize()}:
        """
        Module for all {category} operations.

        Attributes
        ----------
        context_params : {context.capitalize()}QueryParams
            The standard query parameters for {context} data.
        """

        def __init__(self, context_params: {context.capitalize()}QueryParams):
            self.context_params = context_params

        # Add more methods as needed
    '''
    write_file(file_path, content)


def generate_model(context: str, category: str, command: str) -> None:
    """
    Generate the model file for a given context, category, and command.

    Parameters
    ----------
    context : str
        The name of the context.
    category : str
        The name of the category.
    command : str
        The name of the command.

    """
    file_path = Path(f"humbldata/{context}/{category}/{command}/model.py")
    content = f'''
    """
    Context: {context.capitalize()} || Category: {category.capitalize()} || Command: {command.capitalize()}

    A command to perform {command} operations.
    """

    def calc_{command}():
        """
        Calculate the {command}.

        This is a dummy function to serve as an example.
        """
        return "Result of {command} calculation"
    '''
    write_file(file_path, content)


def generate_view(context: str, category: str, command: str) -> None:
    """
    Generate the view file for a given context, category, and command.

    Parameters
    ----------
    context : str
        The name of the context.
    category : str
        The name of the category.
    command : str
        The name of the command.

    """
    file_path = Path(f"humbldata/{context}/{category}/{command}/view.py")
    content = f'''
    """
    Context: {context.capitalize()} || Category: {category.capitalize()} || Command: {command.capitalize()}

    View module for the {command} command.
    """

    def display_{command}_result(result):
        """
        Display the result of the {command} operation.

        This is a dummy function to serve as an example.
        """
        print(f"Result of {command}: {{result}}")
    '''
    write_file(file_path, content)


def generate_helpers(context: str, category: str, command: str) -> None:
    """
    Generate the helpers file for a given context, category, and command.

    Parameters
    ----------
    context : str
        The name of the context.
    category : str
        The name of the category.
    command : str
        The name of the command.

    """
    file_path = Path(f"humbldata/{context}/{category}/{command}/helpers.py")
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
    context, category, command, add_view, add_helpers = prompt_user()

    # Split category into sub-categories
    categories = category.split("/")

    # Create directories
    create_directory(Path(f"humbldata/core/standard_models/{context}"))
    current_path = Path(f"humbldata/core/standard_models/{context}")
    for cat in categories:
        current_path = current_path / cat
        create_directory(current_path)

    create_directory(Path(f"humbldata/{context}"))
    current_path = Path(f"humbldata/{context}")
    for cat in categories:
        current_path = current_path / cat
        create_directory(current_path)
    create_directory(current_path / command)

    # Generate files
    generate_context_files(context)
    generate_command_files(context, category, command)
    generate_context_controller(context)

    # Generate category controllers for each level
    current_category = ""
    for cat in categories:
        current_category = (
            f"{current_category}/{cat}" if current_category else cat
        )
        generate_category_controller(context, current_category)

    generate_model(context, category, command)

    if add_view:
        generate_view(context, category, command)
    if add_helpers:
        generate_helpers(context, category, command)

    print("Files generated successfully!")


if __name__ == "__main__":
    main()
