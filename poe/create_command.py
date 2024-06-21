import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)


def create_directory(path):
    path_obj = Path(path)
    if not path_obj.exists():
        path_obj.mkdir(parents=True)
        logging.info(f"Created directory: {path}")
    else:
        logging.info(f"Directory already exists: {path}")


def create_file(path, content=""):
    if not Path(path).exists():
        with Path(path).open("w") as file:
            file.write(content)
        logging.info(f"Created file: {path}")
    else:
        logging.info(f"File already exists: {path}")


def main():
    context = input("Enter the context name: ")
    category = input("Enter the category name: ")
    command = input("Enter the command name: ")

    base_path = Path("src", "humbldata", context)
    category_path = base_path / category
    command_file_path = category_path / f"{command}.py"

    # Create directories
    create_directory(base_path)
    create_directory(category_path)

    # Create command file with a basic template
    command_template = f"""from humbldata.core.standard_models.{context}_query_params import {context.capitalize()}QueryParams
from humbldata.core.standard_models.{context}_data import {context.capitalize()}Data

class {category.capitalize()}:
    def __init__(self, context_params: {context.capitalize()}QueryParams):
        self.context_params = context_params

    def {command}(self, command_params: dict) -> {context.capitalize()}Data:
        # Core logic for {command}
        # This is a placeholder for the actual implementation
        data = {context.capitalize()}Data(
            # Populate with actual data
        )
        return data
"""
    create_file(command_file_path, command_template)

    # Create models directory and files if they don't exist
    models_path = base_path / "models"
    create_directory(models_path)

    query_params_file_path = models_path / f"{context}_query_params.py"
    data_file_path = models_path / f"{context}_data.py"
    query_params_file_path = models_path / f"{context}_query_params.py"
    data_file_path = models_path / f"{context}_data.py"

    query_params_template = f"""from pydantic import BaseModel

class {context.capitalize()}QueryParams(BaseModel):
    # Define the structure of the query params
    # This is a placeholder for the actual implementation
    pass
"""
    data_template = f"""from pydantic import BaseModel

class {context.capitalize()}Data(BaseModel):
    # Define the structure of the data
    # This is a placeholder for the actual implementation
    pass
"""

    create_file(query_params_file_path, query_params_template)
    create_file(data_file_path, data_template)


if __name__ == "__main__":
    main()
