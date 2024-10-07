
"""
HumblCompass Standard Model.

Context: Toolbox || Category: Fundamental || Command: humbl_compass.

This module is used to define the QueryParams and Data model for the
HumblCompass command.
"""

from typing import Literal, TypeVar

import pandera.polars as pa
import polars as pl
from pydantic import Field, field_validator

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.utils.env import Env
from humbldata.core.utils.logger import log_start_end, setup_logger

env = Env()
Q = TypeVar("Q", bound=ToolboxQueryParams)
logger = setup_logger("HumblCompassFetcher", level=env.LOGGER_LEVEL)

HUMBLCOMPASS_QUERY_DESCRIPTIONS = {
    "example_field1": "Description for example field 1",
    "example_field2": "Description for example field 2",
}


class HumblCompassQueryParams(QueryParams):
    """
    QueryParams model for the HumblCompass command, a Pydantic v2 model.

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
        description=HUMBLCOMPASS_QUERY_DESCRIPTIONS.get("example_field1", ""),
    )
    example_field2: bool = Field(
        default=True,
        title="Example Field 2",
        description=HUMBLCOMPASS_QUERY_DESCRIPTIONS.get("example_field2", ""),
    )

    @field_validator("example_field1")
    @classmethod
    def validate_example_field1(cls, v: str) -> str:
        return v.upper()


class HumblCompassData(Data):
    """
    Data model for the humbl_compass command, a Pandera.Polars Model.

    This Data model is used to validate data in the `.transform_data()` method of the `HumblCompassFetcher` class.
    """

    example_column: pl.Date = Field(
        default=None,
        title="Example Column",
        description="Description for example column",
    )

class HumblCompassFetcher:
    """
    Fetcher for the HumblCompass command.

    Parameters
    ----------
    context_params : ToolboxQueryParams
        The context parameters for the Toolbox query.
    command_params : HumblCompassQueryParams
        The command-specific parameters for the HumblCompass query.

    Attributes
    ----------
    context_params : ToolboxQueryParams
        Stores the context parameters passed during initialization.
    command_params : HumblCompassQueryParams
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
        Transforms the command-specific data according to the HumblCompass logic.
    fetch_data()
        Execute TET Pattern.

    Returns
    -------
    HumblObject
        results : HumblCompassData
            Serializable results.
        provider : Literal['fmp', 'intrinio', 'polygon', 'tiingo', 'yfinance']
            Provider name.
        warnings : Optional[List[Warning_]]
            List of warnings.
        chart : Optional[Chart]
            Chart object.
        context_params : ToolboxQueryParams
            Context-specific parameters.
        command_params : HumblCompassQueryParams
            Command-specific parameters.
    """

    def __init__(
        self,
        context_params: ToolboxQueryParams,
        command_params: HumblCompassQueryParams,
    ):
        """
        Initialize the HumblCompassFetcher with context and command parameters.

        Parameters
        ----------
        context_params : ToolboxQueryParams
            The context parameters for the Toolbox query.
        command_params : HumblCompassQueryParams
            The command-specific parameters for the HumblCompass query.
        """
        self.context_params = context_params
        self.command_params = command_params

    def transform_query(self):
        """
        Transform the command-specific parameters into a query.

        If command_params is not provided, it initializes a default HumblCompassQueryParams object.
        """
        if not self.command_params:
            self.command_params = HumblCompassQueryParams()
        else:
            self.command_params = HumblCompassQueryParams(**self.command_params)

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
        Transform the command-specific data according to the humbl_compass logic.

        Returns
        -------
        pl.DataFrame
            The transformed data as a Polars DataFrame
        """
        # Implement data transformation logic here
        self.transformed_data = HumblCompassData(self.data)
        self.transformed_data = self.transformed_data.serialize()
        return self

    @log_start_end(logger=logger)
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

        if not hasattr(self.context_params, "warnings"):
            self.context_params.warnings = []

        return HumblObject(
            results=self.transformed_data,
            provider=self.context_params.provider,
            warnings=self.context_params.warnings,
            chart=None,
            context_params=self.context_params,
            command_params=self.command_params,
        )

