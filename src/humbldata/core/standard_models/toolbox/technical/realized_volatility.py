"""
Volatility Standard Model.

Context: Toolbox || Category: Technical || Command: **Volatility**.

This module is used to define the QueryParams and Data model for the
Volatility command.
"""

from typing import ClassVar, TypeVar


from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.toolbox import ToolboxQueryParams

Q = TypeVar("Q", bound=ToolboxQueryParams)


class RealizedVolatilityQueryParams(QueryParams):
    """
    QueryParams for the Realized Volatility command.
    """


class RealizedVolatilityData(Data):
    """
    Data model for the Realized Volatility command.
    """


class RealizedVolatilityFetcher(RealizedVolatilityQueryParams):
    """
    Fetcher for the Realized Volatility command.
    """

    data_list: ClassVar[list[RealizedVolatilityData]] = []

    def __init__(
        self,
        context_params: ToolboxQueryParams,
        command_params: RealizedVolatilityQueryParams,
    ):
        self._context_params = context_params
        self._command_params = command_params

    def transform_query(self):
        """Transform the params to the command-specific query."""

    def extract_data(self):
        """Extract the data from the provider."""
        # Assuming 'obb' is a predefined object in your context
        df = (
            obb.equity.price.historical(
                symbol=self.context_params.symbol,
                start_date=str(self.context_params.start_date),
                end_date=str(self.context_params.end_date),
                provider=self.command_params.provider,
                verbose=not self.command_params.kwargs.get("silent", False),
                **self.command_params.kwargs,
            )
            .to_df()
            .reset_index()
        )
        return df

    def transform_data(self):
        """Transform the command-specific data."""
        # Placeholder for data transformation logic

    def fetch_data(self):
        """Execute the TET pattern."""
        # Call the methods in the desired order
        query = self.transform_query()
        raw_data = (
            self.extract_data()
        )  # This should use 'query' to fetch the data
        transformed_data = (
            self.transform_data()
        )  # This should transform 'raw_data'

        # Validate with VolatilityData, unpack dict into pydantic row by row
        return transformed_data
