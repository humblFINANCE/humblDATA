
"""
user table Standard Model.

Context: Portfolio || Category: Analytics || Command: user table.

This module is used to define the QueryParams and Data model for the
user table command.
"""

from typing import Literal, TypeVar

import pandera.polars as pa
import polars as pl
from pydantic import Field, field_validator

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.portfolio import PortfolioQueryParams

Q = TypeVar("Q", bound=PortfolioQueryParams)

USER TABLE_QUERY_DESCRIPTIONS = {
    "example_field1": "Description for example field 1",
    "example_field2": "Description for example field 2",
}


class user tableQueryParams(QueryParams):
    """
    QueryParams model for the user table command, a Pydantic v2 model.

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
        description=USER TABLE_QUERY_DESCRIPTIONS.get("example_field1", ""),
    )
    example_field2: bool = Field(
        default=True,
        title="Example Field 2",
        description=USER TABLE_QUERY_DESCRIPTIONS.get("example_field2", ""),
    )

    @field_validator("example_field1")
    @classmethod
    def validate_example_field1(cls, v: str) -> str:
        return v.upper()


class user tableData(Data):
    """
    Data model for the user table command, a Pandera.Polars Model.
    """

    example_column: pl.Date = pa.Field(
        default=None,
        title="Example Column",
        description="Description for example column",
    )

class user tableFetcher:
    """
    Fetcher for the user table command.

    Parameters
    ----------
    context_params : PortfolioQueryParams
        The context parameters for the Portfolio query.
    command_params : User tableQueryParams
        The command-specific parameters for the user table query.

    Attributes
    ----------
    context_params : PortfolioQueryParams
        Stores the context parameters passed during initialization.
    command_params : User tableQueryParams
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
        Transforms the command-specific data according to the user table logic.
    fetch_data()
        Execute TET Pattern.

    Returns
    -------
    HumblObject
        results : user tableData
            Serializable results.
        provider : Literal['fmp', 'intrinio', 'polygon', 'tiingo', 'yfinance']
            Provider name.
        warnings : Optional[List[Warning_]]
            List of warnings.
        chart : Optional[Chart]
            Chart object.
        context_params : PortfolioQueryParams
            Context-specific parameters.
        command_params : User tableQueryParams
            Command-specific parameters.
    """

    def __init__(
        self,
        context_params: PortfolioQueryParams,
        command_params: User tableQueryParams,
    ):
        """
        Initialize the user tableFetcher with context and command parameters.

        Parameters
        ----------
        context_params : PortfolioQueryParams
            The context parameters for the Portfolio query.
        command_params : User tableQueryParams
            The command-specific parameters for the User table query.
        """
        self.context_params = context_params
        self.command_params = command_params

    def transform_query(self):
        """
        Transform the command-specific parameters into a query.

        If command_params is not provided, it initializes a default user tableQueryParams object.
        """
        if not self.command_params:
            self.command_params = None
            # Set Default Arguments
            self.command_params: User tableQueryParams = (
                User tableQueryParams()
            )
        else:
            self.command_params: User tableQueryParams = (
                User tableQueryParams(**self.command_params)
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
        Transform the command-specific data according to the user table logic.

        Returns
        -------
        pl.DataFrame
            The transformed data as a Polars DataFrame
        """
        # Implement data transformation logic here
        self.transformed_data = User tableData(self.data)
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

