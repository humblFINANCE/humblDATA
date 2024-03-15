"""
Mandelbrot Channel Standard Model.

Context: Toolbox || Category: Technical || Command: Mandelbrot Channel.

This module is used to define the QueryParams and Data model for the
Mandelbrot Channel command.
"""

import datetime as dt
from typing import TypeVar

from openbb import obb
from pydantic import Field

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.toolbox import ToolboxQueryParams

Q = TypeVar("Q", bound=ToolboxQueryParams)


class MandelbrotChannelQueryParams(QueryParams):
    """
    QueryParams for the Mandelbrot Channel command.
    """


class MandelbrotChannelData(Data):
    """
    Data model for the Mandelbrot Channel command.
    """

    date: dt.date | dt.datetime = Field(
        default=None,
        title="Date",
        description="The date of the data point.",
    )
    symbol: str = Field(
        default=None,
        title="Symbol",
        description="The stock symbol.",
    )
    bottom_price: float = Field(
        default=None,
        title="Bottom Price",
        description="The bottom price in the Mandelbrot Channel.",
    )
    recent_price: float = Field(
        default=None,
        title="Recent Price",
        description="The most recent price within the Mandelbrot Channel.",
    )
    top_price: float = Field(
        default=None,
        title="Top Price",
        description="The top price in the Mandelbrot Channel.",
    )


class MandelbrotChannelFetcher(
    MandelbrotChannelQueryParams, MandelbrotChannelData
):
    """
    Fetcher for the Mandelbrot Channel command.
    """

    def __init__(
        self,
        context_params: ToolboxQueryParams,
        command_params: MandelbrotChannelQueryParams,
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
            ).to_polars()
        ).drop(["dividends", "stock_splits"], axis=1)
        return df

    def transform_data(self):
        """Transform the command-specific data."""
        # Placeholder for data transformation logic

    def fetch_data(self):
        # Call the methods in the desired order
        query = self.transform_query()
        raw_data = (
            self.extract_data()
        )  # This should use 'query' to fetch the data
        transformed_data = (
            self.transform_data()
        )  # This should transform 'raw_data'

        # Validate with MandelbrotChannelData, unpack dict into pydantic row by row
        return transformed_data
