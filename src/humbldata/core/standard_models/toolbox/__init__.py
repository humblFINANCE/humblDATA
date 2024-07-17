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
import logging
import re
from datetime import datetime, timedelta
from typing import Literal

import pandera as pa
import polars as pl
import pytz
from pydantic import Field, field_validator, model_validator

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.utils.constants import OBB_EQUITY_PRICE_HISTORICAL_PROVIDERS
from humbldata.core.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from humbldata.core.utils.env import Env
from humbldata.core.utils.logger import setup_logger

env = Env()
logger = setup_logger(name="ToolboxQueryParams", level=env.LOGGER_LEVEL)


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
    membership : str, default="anonymous"
        The membership level of the user.

    Methods
    -------
    upper_symbol(cls, v: Union[str, list[str], set[str]]) -> Union[str, list[str]]
        A Pydantic `@field_validator()` that converts the stock symbol to
        uppercase. If a list or set of symbols is provided, each symbol in the
        collection is converted to uppercase and returned as a comma-separated
        string.
    validate_interval(cls, v: str) -> str
        A Pydantic `@field_validator()` that validates the interval format.
        Ensures the interval is a number followed by one of 's', 'm', 'h', 'd', 'W', 'M', 'Q', 'Y'.
    validate_date_format(cls, v: str) -> str
        A Pydantic `@field_validator()` that validates the date format to ensure it is YYYY-MM-DD.
    validate_start_date(self) -> 'ToolboxQueryParams'
        A Pydantic `@model_validator()` that validates and adjusts the start date based on membership level.

    Raises
    ------
    ValueError
        If the `symbol` parameter is a list and not all elements are strings, or
        if `symbol` is not a string, list, or set.
        If the `interval` format is invalid.
        If the `date` format is invalid.

    Notes
    -----
    A Pydantic v2 Model

    """

    symbols: str | list[str] = Field(
        default=["AAPL"],
        title="Symbols/Tickers",
        description=QUERY_DESCRIPTIONS.get("symbols", ""),
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
    membership: Literal[
        "anonymous", "peon", "premium", "power", "permanent", "admin"
    ] = Field(
        default="anonymous",
        title="Membership",
        description=QUERY_DESCRIPTIONS.get("membership", ""),
    )

    @field_validator("symbols", mode="before", check_fields=False)
    @classmethod
    def upper_symbol(cls, v: str | list[str] | set[str]) -> list[str]:
        """
        Convert the stock symbols to uppercase and remove empty strings.

        Parameters
        ----------
        v : Union[str, List[str], Set[str]]
            The stock symbol or collection of symbols to be converted.

        Returns
        -------
        List[str]
            A list of uppercase stock symbols with empty strings removed.
        """
        # Handle empty inputs
        if not v:
            return []

        # If v is a string, split it by commas into a list. Otherwise, ensure it's a list.
        v = v.split(",") if isinstance(v, str) else list(v)

        # Convert all elements to uppercase, trim whitespace, and remove empty strings
        valid_symbols = [
            symbol.strip().upper() for symbol in v if symbol.strip()
        ]

        if not valid_symbols:
            msg = "At least one valid symbol (str) must be provided"
            raise ValueError(msg)

        return valid_symbols

    @field_validator("interval", mode="before", check_fields=False)
    @classmethod
    def validate_interval(cls, v: str) -> str:
        """
        Validate the interval format.

        Parameters
        ----------
        v : str
            The interval string to be validated.

        Returns
        -------
        str
            The validated interval string.

        Raises
        ------
        ValueError
            If the interval format is invalid.
        """
        if not re.match(r"^\d*[smhdWMQY]$", v):
            msg = "Invalid interval format. Must be a number followed by one of 's', 'm', 'h', 'd', 'W', 'M', 'Q', 'Y'."
            raise ValueError(msg)
        return v

    @field_validator(
        "start_date", "end_date", mode="before", check_fields=False
    )
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """
        Validate the date format to ensure it is YYYY-MM-DD.

        Parameters
        ----------
        v : str
            The date string to be validated.

        Returns
        -------
        str
            The validated date string.

        Raises
        ------
        ValueError
            If the date format is invalid.
        """
        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$", v):
            msg = "Invalid date format. Must be YYYY-MM-DD with MM between 01 and 12, and DD between 01 and 31."
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_start_date(self) -> "ToolboxQueryParams":
        end_date = datetime.now().date()

        start_date_mapping = {
            "anonymous": end_date - timedelta(days=365),
            "peon": end_date - timedelta(days=730),
            "premium": end_date - timedelta(days=1825),
            "power": end_date - timedelta(days=7300),
            "permanent": end_date - timedelta(days=10680),
            "admin": end_date - timedelta(days=27000),
        }

        allowed_start_date = start_date_mapping.get(
            self.membership.lower(), end_date - timedelta(days=365)
        )

        # Convert self.start_date to datetime.date if it's a string
        if isinstance(self.start_date, str):
            try:
                start_date = (
                    datetime.strptime(self.start_date, "%Y-%m-%d")
                    .replace(tzinfo=dt.UTC)
                    .date()
                )
            except ValueError as err:
                msg = f"Invalid date format for start_date: {self.start_date}. Expected format: YYYY-MM-DD"
                raise ValueError(msg) from err
        elif isinstance(self.start_date, datetime):
            start_date = self.start_date.date()
        elif isinstance(self.start_date, dt.date):
            start_date = self.start_date
        else:
            msg = f"Unsupported type for start_date: {type(self.start_date)}"
            raise TypeError(msg)

        if start_date < allowed_start_date:
            logging.warning(
                f"Start date adjusted to {allowed_start_date} based on {self.membership} membership."
            )
            self.start_date = allowed_start_date.strftime("%Y-%m-%d")
        else:
            self.start_date = start_date.strftime("%Y-%m-%d")

        return self


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
