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


def clean_name(name: str, case: str = "camelCase") -> str:
    """
    Clean and format a name to follow the specified convention.

    Parameters
    ----------
    name : str
        The name to clean and format.
    case : str
        The case of formatting to apply. Can be "camelCase", "snake_case", or "PascalCase".
        Defaults to "camelCase".

    Returns
    -------
    str
        The cleaned and formatted name.
    """
    # Replace any non-alphanumeric characters (except underscores) with spaces
    name = re.sub(r"[^\w\s]", " ", name)
    # Split the name into words
    words = name.split()

    if case.lower() == "camelcase":
        return words[0].lower() + "".join(
            word.capitalize() for word in words[1:]
        )
    elif case.lower() == "snake_case":
        return "_".join(word.lower() for word in words)
    elif case.lower() == "pascalcase":
        return "".join(word.capitalize() for word in words)
    else:
        msg = (
            "Invalid case. Must be 'camelCase', 'snake_case', or 'PascalCase'."
        )
        raise ValueError(msg)


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
**Context: {clean_name(context, case="PascalCase")}**.

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
        / "model.py"
    )
    content = f'''
"""
**Context: {clean_name(context, case="PascalCase")} || Category: {clean_name(category, case="PascalCase")} || Command: {clean_name(command, case="PascalCase")}**.

The {clean_name(command, case="PascalCase")} Command Module.
"""

def {clean_name(command, case="snake_case")}():
    """
    Context: {clean_name(context, case="PascalCase")} || Category: {clean_name(category, case="PascalCase")} ||| **Command: {clean_name(command, case="PascalCase")}**.

    Execute the {clean_name(command, case="PascalCase")} command.

    Parameters
    ----------

    Returns
    -------
    """
    pass
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
**Context: {clean_name(context, case="PascalCase")}**.

The {clean_name(context, case="PascalCase")} Controller Module.
"""

from humbldata.core.standard_models.{context.lower()} import {clean_name(context, case="PascalCase")}QueryParams
from humbldata.{context.lower()}.{category.lower()}.{category.lower()}_controller import {clean_name(category, case="PascalCase")}


class {clean_name(context, case="PascalCase")}({clean_name(context, case="PascalCase")}QueryParams):
    """
    A top-level {clean_name(context, case="PascalCase")} controller for data analysis tools in `humblDATA`.

    This module serves as the primary controller, routing user-specified
    {clean_name(context, case="PascalCase")}QueryParams as core arguments that are used to fetch time series
    data.

    The `{clean_name(context)}` controller also gives access to all sub-modules and their
    functions.

    It is designed to facilitate the collection of data across various types such as
    stocks, options, or alternative time series by requiring minimal input from the user.

    Submodules
    ----------
    The `{clean_name(context, case="PascalCase")}` controller is composed of the following submodules:

    - `{category.lower()}`:

    Parameters
    ----------
    # Add your {clean_name(category, case="PascalCase")}QueryParams parameters here

    Parameter Notes
    -----
    The parameters are the `{clean_name(context, case="PascalCase")}QueryParams`. They are used
    for data collection further down the pipeline in other commands.
    Intended to execute operations on core data sets. This approach enables
    composable and standardized querying while accommodating data-specific
    collection logic.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the {clean_name(context, case="PascalCase")} module.

        This method does not take any parameters and does not return anything.
        """
        super().__init__(*args, **kwargs)

    @property
    def {category.lower()}(self):
        """
        The {category.lower()} submodule of the {clean_name(context, case="PascalCase")} controller.

        Access to all the {clean_name(category, case="PascalCase")} indicators. When the {clean_name(context, case="PascalCase")} class is
        instantiated the parameters are initialized with the {clean_name(context, case="PascalCase")}QueryParams
        class, which hold all the fields needed for the context_params, like the
        symbol, interval, start_date, and end_date.
        """
        return {clean_name(category, case="PascalCase")}(context_params=self)
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
"""Context: {clean_name(context, case="PascalCase")} || **Category: {clean_name(category, case="PascalCase")}**.

A controller to manage and compile all of the {clean_name(category, case="PascalCase")} models
available in the `{clean_name(context)}` context. This will be passed as a
`@property` to the `{clean_name(context)}()` class, giving access to the
{clean_name(category, case="PascalCase")} module and its functions.
"""
from humbldata.core.standard_models.{context.lower()} import {clean_name(context, case="PascalCase")}QueryParams
from humbldata.core.standard_models.{context.lower()}.{category.lower()}.{clean_name(command, case="snake_case")} import (
    {clean_name(command, case="PascalCase")}QueryParams,
)


class {clean_name(category, case="PascalCase")}:
    """
    Module for all {clean_name(category, case="PascalCase")} analysis.

    Attributes
    ----------
    context_params : {clean_name(context, case="PascalCase")}QueryParams
        The standard query parameters for {clean_name(context)} data.

    Methods
    -------
    {clean_name(command, case="snake_case")}(command_params: {clean_name(command, case="PascalCase")}QueryParams)
        Execute the {clean_name(command, case="PascalCase")} command.

    """

    def __init__(self, context_params: {clean_name(context, case="PascalCase")}QueryParams):
        self.context_params = context_params

    def {clean_name(command, case="snake_case")}(self, **kwargs: {clean_name(command, case="PascalCase")}QueryParams):
        """
        Execute the {clean_name(command, case="PascalCase")} command.

        Explain the functionality...
        """
        from humbldata.core.standard_models.{context.lower()}.{category.lower()}.{clean_name(command, case="snake_case")} import (
            {clean_name(command, case="PascalCase")}Fetcher,
        )

        # Instantiate the Fetcher with the query parameters
        fetcher = {clean_name(command, case="PascalCase")}Fetcher(
            context_params=self.context_params, command_params=kwargs
        )

        # Use the fetcher to get the data
        return fetcher.fetch_data()
'''
    write_file(file_path, content.strip())

    # Create __init__.py in the category directory
    init_file_path = file_path.parent / "__init__.py"
    write_file(init_file_path, "")


def generate_standard_model(
    project_root: Path, context: str, category: str, command: str
) -> None:
    """
    Generate the model files for both context and command.

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
    # Generate context standard model
    context_file_path = (
        project_root
        / "src"
        / "humbldata"
        / "core"
        / "standard_models"
        / context
        / "__init__.py"
    )
    context_content = f'''
"""
Context: {clean_name(context, case="PascalCase")} || **Category: Standardized Framework Model**.

This module defines the QueryParams and Data classes for the {clean_name(context, case="PascalCase")} context.
"""

from typing import Optional

from pydantic import Field, field_validator

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.query_params import QueryParams


class {clean_name(context, case="PascalCase")}QueryParams(QueryParams):
    """
    Query parameters for the {clean_name(context, case="PascalCase")}Controller.

    This class defines the query parameters used by the {clean_name(context, case="PascalCase")}Controller.

    Parameters
    ----------
    example_field1 : str
        An example field.
    example_field2 : Optional[int]
        Another example field.
    """

    example_field1: str = Field(
        default="default_value",
        title="Example Field 1",
        description="Description for example field 1",
    )
    example_field2: Optional[int] = Field(
        default=None,
        title="Example Field 2",
        description="Description for example field 2",
    )

    @field_validator("example_field1")
    @classmethod
    def validate_example_field1(cls, v: str) -> str:
        return v.upper()


class {clean_name(context, case="PascalCase")}Data(Data):
    """
    The Data for the {clean_name(context, case="PascalCase")}Controller.
    """

    # Add your data model fields here
    pass
'''
    write_file(context_file_path, context_content)

    # Generate command standard model
    command_file_path = (
        project_root
        / "src"
        / "humbldata"
        / "core"
        / "standard_models"
        / context
        / category
        / f"{command}.py"
    )
    command_content = f'''
"""
{clean_name(command, case="PascalCase")} Standard Model.

Context: {clean_name(context, case="PascalCase")} || Category: {clean_name(category, case="PascalCase")} || Command: {clean_name(command, case="PascalCase")}.

This module is used to define the QueryParams and Data model for the
{clean_name(command, case="PascalCase")} command.
"""

from typing import Literal, TypeVar

import pandera.polars as pa
import polars as pl
from pydantic import Field, field_validator

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.{context} import {clean_name(context, case="PascalCase")}QueryParams

Q = TypeVar("Q", bound={clean_name(context, case="PascalCase")}QueryParams)

{clean_name(command, case="PascalCase").upper()}_QUERY_DESCRIPTIONS = {{
    "example_field1": "Description for example field 1",
    "example_field2": "Description for example field 2",
}}


class {clean_name(command, case="PascalCase")}QueryParams(QueryParams):
    """
    QueryParams model for the {clean_name(command, case="PascalCase")} command, a Pydantic v2 model.

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
        description={clean_name(command, case="PascalCase").upper()}_QUERY_DESCRIPTIONS.get("example_field1", ""),
    )
    example_field2: bool = Field(
        default=True,
        title="Example Field 2",
        description={clean_name(command, case="PascalCase").upper()}_QUERY_DESCRIPTIONS.get("example_field2", ""),
    )

    @field_validator("example_field1")
    @classmethod
    def validate_example_field1(cls, v: str) -> str:
        return v.upper()


class {clean_name(command, case="PascalCase")}Data(Data):
    """
    Data model for the {clean_name(command, case="PascalCase")} command, a Pandera.Polars Model.
    """

    example_column: pl.Date = pa.Field(
        default=None,
        title="Example Column",
        description="Description for example column",
    )

class {clean_name(command, case="PascalCase")}Fetcher:
    """
    Fetcher for the {clean_name(command, case="PascalCase")} command.

    Parameters
    ----------
    context_params : {clean_name(context, case="PascalCase")}QueryParams
        The context parameters for the {clean_name(context, case="PascalCase")} query.
    command_params : {clean_name(command, case="PascalCase")}QueryParams
        The command-specific parameters for the {clean_name(command, case="PascalCase")} query.

    Attributes
    ----------
    context_params : {clean_name(context, case="PascalCase")}QueryParams
        Stores the context parameters passed during initialization.
    command_params : {clean_name(command, case="PascalCase")}QueryParams
        Stores the command-specific parameters passed during initialization.
    data : pl.DataFrame
        The raw data extracted from the data provider, before transformation.

    Methods
    -------
    transform_query()
        Transform the command-specific parameters into a query.
    extract_data()
        Extracts the data from the provider and returns it as a Polars DataFrame.
    transform_data()
        Transforms the command-specific data according to the {clean_name(command, case="PascalCase")} logic.
    fetch_data()
        Execute TET Pattern.

    Returns
    -------
    HumblObject
        results : {clean_name(command, case="PascalCase")}Data
            Serializable results.
        provider : Literal['fmp', 'intrinio', 'polygon', 'tiingo', 'yfinance']
            Provider name.
        warnings : Optional[List[Warning_]]
            List of warnings.
        chart : Optional[Chart]
            Chart object.
        context_params : {clean_name(context, case="PascalCase")}QueryParams
            Context-specific parameters.
        command_params : {clean_name(command, case="PascalCase")}QueryParams
            Command-specific parameters.
    """

    def __init__(
        self,
        context_params: {clean_name(context, case="PascalCase")}QueryParams,
        command_params: {clean_name(command, case="PascalCase")}QueryParams,
    ):
        """
        Initialize the {clean_name(command, case="PascalCase")}Fetcher with context and command parameters.

        Parameters
        ----------
        context_params : {clean_name(context, case="PascalCase")}QueryParams
            The context parameters for the {clean_name(context, case="PascalCase")} query.
        command_params : {clean_name(command, case="PascalCase")}QueryParams
            The command-specific parameters for the {clean_name(command, case="PascalCase")} query.
        """
        self.context_params = context_params
        self.command_params = command_params

    def transform_query(self):
        """
        Transform the command-specific parameters into a query.

        If command_params is not provided, it initializes a default {clean_name(command, case="PascalCase")}QueryParams object.
        """
        if not self.command_params:
            self.command_params = None
            # Set Default Arguments
            self.command_params: {clean_name(command, case="PascalCase")}QueryParams = (
                {clean_name(command, case="PascalCase")}QueryParams()
            )
        else:
            self.command_params: {clean_name(command, case="PascalCase")}QueryParams = (
                {clean_name(command, case="PascalCase")}QueryParams(**self.command_params)
            )

    def extract_data(self):
        """
        Extract the data from the provider and returns it as a Polars DataFrame.

        Returns
        -------
        pl.DataFrame
            The extracted data as a Polars DataFrame.
        """
        # Implement data extraction logic here
        self.data = pl.DataFrame()
        return self

    def transform_data(self):
        """
        Transform the command-specific data according to the {clean_name(command, case="PascalCase")} logic.

        Returns
        -------
        pl.DataFrame
            The transformed data as a Polars DataFrame
        """
        # Implement data transformation logic here
        self.transformed_data = {clean_name(command, case="PascalCase")}Data(self.data)
        self.transformed_data = self.transformed_data.serialize()
        return self

    def fetch_data(self):
        """
        Execute TET Pattern.

        This method executes the query transformation, data fetching and
        transformation process by first calling `transform_query` to prepare the query parameters, then
        extracting the raw data using `extract_data` method, and finally
        transforming the raw data using `transform_data` method.

        Returns
        -------
        HumblObject
            The HumblObject containing the transformed data and metadata.
        """
        self.transform_query()
        self.extract_data()
        self.transform_data()

        return HumblObject(
            results=self.transformed_data,
            provider=self.context_params.provider,
            warnings=None,
            chart=None,
            context_params=self.context_params,
            command_params=self.command_params,
        )

'''
    write_file(command_file_path, command_content)

    # Create __init__.py in the category directory
    init_file_path = command_file_path.parent / "__init__.py"
    write_file(init_file_path, "")


def generate_helpers(
    project_root: Path, context: str, category: str, command: str
) -> None:
    """
    Generate the helpers.py file for the command.

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
    helpers_file_path = (
        project_root
        / "src"
        / "humbldata"
        / context
        / category
        / command
        / "helpers.py"
    )
    helpers_content = f'''
"""
**Context: {clean_name(context, case="PascalCase")} || Category: {clean_name(category, case="PascalCase")} || Command: {clean_name(command, case="PascalCase")}**.

The {clean_name(command, case="PascalCase")} Helpers Module.
"""

def helper_function():
    return "Helper function result"
'''
    write_file(helpers_file_path, helpers_content)

    # Create __init__.py in the command directory
    init_file_path = helpers_file_path.parent / "__init__.py"
    write_file(init_file_path, "")


def generate_view(
    project_root: Path, context: str, category: str, command: str
) -> None:
    """
    Generate the view.py file for the command.

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
    view_file_path = (
        project_root
        / "src"
        / "humbldata"
        / context
        / category
        / command
        / "view.py"
    )
    view_content = f'''
"""
**Context: {clean_name(context, case="PascalCase")} || Category: {clean_name(category, case="PascalCase")} || Command: {clean_name(command, case="PascalCase")}**.

The {clean_name(command, case="PascalCase")} View Module.
"""

from typing import List

import plotly.graph_objs as go
import polars as pl

from humbldata.core.standard_models.abstract.chart import Chart, ChartTemplate


def create_example_plot(
    data: pl.DataFrame,
    template: ChartTemplate = ChartTemplate.plotly,
) -> go.Figure:
    """
    Generate an example plot from the provided data.

    Parameters
    ----------
    data : pl.DataFrame
        The dataframe containing the data to be plotted.
    template : ChartTemplate
        The template to be used for styling the plot.

    Returns
    -------
    go.Figure
        A plotly figure object representing the example plot.
    """
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data.select("x_column").to_series(),
            y=data.select("y_column").to_series(),
            name="Example Data",
            line=dict(color="blue"),
        )
    )
    fig.update_layout(
        title="Example Plot",
        xaxis_title="X Axis",
        yaxis_title="Y Axis",
        template=template,
    )
    return fig


def generate_plots(
    data: pl.LazyFrame,
    template: ChartTemplate = ChartTemplate.plotly,
) -> List[Chart]:
    """
    Context: {clean_name(context, case="PascalCase")} || Category: {clean_name(category, case="PascalCase")} || Command: {clean_name(command, case="PascalCase")} || **Function: generate_plots()**.

    Generate plots from the given dataframe.

    Parameters
    ----------
    data : pl.LazyFrame
        The LazyFrame containing the data to be plotted.
    template : ChartTemplate
        The template/theme to use for the plotly figure.

    Returns
    -------
    List[Chart]
        A list of Chart objects, each representing a plot.
    """
    collected_data = data.collect()
    plot = create_example_plot(collected_data, template)
    return [Chart(content=plot.to_plotly_json(), fig=plot)]
'''
    write_file(view_file_path, view_content)

    # Create __init__.py in the command directory
    init_file_path = view_file_path.parent / "__init__.py"
    write_file(init_file_path, "")


def main() -> None:
    """
    Orchestrate the creation of new command files & directories.

    This function ties together all the helper functions to create a new command.
    This is to be used with `poethepoet` to create a new command.

    """
    project_root = get_project_root()
    context, category, command, add_view, add_helpers = prompt_user()

    command = clean_name(command, case="snake_case")

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
