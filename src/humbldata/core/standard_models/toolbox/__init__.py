"""
Context: Toolbox || **Category: Standardized Framework Model**.

This module defines the QueryParams and Data classes for the Toolbox context.
THis is where all of the context(s) of your project go. The STANDARD MODELS for
categories and subsequent commands are nested here.

Classes
-------
ToolboxQueryParams
    Query parameters for the ToolboxController.
ToolboxData
    A Pydantic model that defines the data returned by the ToolboxController.

Attributes
----------
symbol : str
    The symbol/ticker of the stock.
interval : Optional[str]
    The interval of the data. Defaults to '1d'.
start_date : str
    The start date of the data.
end_date : str
    The end date of the data.
"""

import datetime as dt
from typing import Optional

import pandera as pa
import polars as pl
import pytz
from pydantic import Field, field_validator

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.utils.constants import OBB_EQUITY_PRICE_HISTORICAL_PROVIDERS
from humbldata.core.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)


class ToolboxQueryParams(QueryParams):
    """
    Query parameters for the ToolboxController.

    This class defines the query parameters used by the ToolboxController,
    including the stock symbol, data interval, start date, and end date. It also
    includes a method to ensure the stock symbol is in uppercase.
    If no dates constraints are given, it will collect the MAX amount of data
    available.

    Parameters
    ----------
    symbol : str | list[str] | set[str], default=""
        The symbol or ticker of the stock. You can pass multiple tickers like:
        "AAPL", "AAPL, MSFT" or ["AAPL", "MSFT"]. The input will be converted
        to uppercase.
    interval : str | None, default="1d"
        The interval of the data. Can be None.
    start_date : str, default=""
        The start date for the data query.
    end_date : str, default=""
        The end date for the data query.
    provider : OBB_EQUITY_PRICE_HISTORICAL_PROVIDERS, default="yfinance"
        The data provider to be used for the query.

    Methods
    -------
    upper_symbol(cls, v: Union[str, list[str], set[str]]) -> Union[str, list[str]]
        A Pydantic `@field_validator()` that converts the stock symbol to
        uppercase. If a list or set of symbols is provided, each symbol in the
        collection is converted to uppercase and returned as a comma-separated
        string.

    Raises
    ------
    ValueError
        If the `symbol` parameter is a list and not all elements are strings, or
        if `symbol` is not a string, list, or set.

    Notes
    -----
    A Pydantic v2 Model

    """

    symbol: str | list[str] = Field(
        default="AAPL",
        title="Symbol/Ticker",
        description=QUERY_DESCRIPTIONS.get("symbol", ""),
    )
    interval: str | None = Field(
        default="1d",
        title="Interval",
        description=QUERY_DESCRIPTIONS.get("interval", ""),
    )
    start_date: dt.date | str = Field(
        default_factory=lambda: dt.date(1950, 1, 1),
        title="Start Date",
        description="The starting date for the data query.",
    )
    end_date: dt.date | str = Field(
        default_factory=lambda: dt.datetime.now(
            tz=pytz.timezone("America/New_York")
        ).date(),
        title="End Date",
        description="The ending date for the data query.",
    )
    provider: OBB_EQUITY_PRICE_HISTORICAL_PROVIDERS = Field(
        default="yfinance",
        title="Provider",
        description=QUERY_DESCRIPTIONS.get("provider", ""),
    )

    @field_validator("symbol", mode="before", check_fields=False)
    @classmethod
    def upper_symbol(cls, v: str | list[str] | set[str]) -> str | list[str]:
        """
        Convert the stock symbol to uppercase.

        Parameters
        ----------
        v : Union[str, List[str], Set[str]]
            The stock symbol or collection of symbols to be converted.

        Returns
        -------
        Union[str, List[str]]
            The uppercase stock symbol or a comma-separated string of uppercase
            symbols.
        """
        # If v is a string, split it by commas into a list. Otherwise, ensure it's a list.
        v = v.split(",") if isinstance(v, str) else v

        # Trim whitespace and check if all elements in the list are strings
        if not all(isinstance(item.strip(), str) for item in v):
            msg = "Every element in `symbol` list must be a `str`"
            raise ValueError(msg)

        # Convert all elements to uppercase, trim whitespace, and join them with a comma
        return [symbol.strip().upper() for symbol in v]


class ToolboxData(Data):
    """
    The Data for the ToolboxController.

    WIP: I'm thinking that this is the final layer around which the
    HumblDataObject will be returned to the user, with all necessary information
    about the query, command, data and charts that they should want.
    This HumblDataObject will return values in json/dict format, with methods
    to allow transformation into polars_df, pandas_df, a list, a dict...
    """

    date: pl.Date = pa.Field(
        default=None,
        title="Date",
        description=DATA_DESCRIPTIONS.get("date", ""),
    )
    open: float = pa.Field(
        default=None,
        title="Open",
        description=DATA_DESCRIPTIONS.get("open", ""),
    )
    high: float = pa.Field(
        default=None,
        title="High",
        description=DATA_DESCRIPTIONS.get("high", ""),
    )
    low: float = pa.Field(
        default=None,
        title="Low",
        description=DATA_DESCRIPTIONS.get("low", ""),
    )
    close: float = pa.Field(
        default=None,
        title="Close",
        description=DATA_DESCRIPTIONS.get("close", ""),
    )
    volume: int = pa.Field(
        default=None,
        title="Volume",
        description=DATA_DESCRIPTIONS.get("volume", ""),
    )
