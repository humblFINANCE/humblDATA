"""
Context: Portfolio || **Category: Analytics**.

This module defines the QueryParams and Data classes for the Portfolio context.
"""

from typing import Literal

import polars as pl
from pydantic import Field, field_validator

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.utils.constants import OBB_EQUITY_PRICE_HISTORICAL_PROVIDERS
from humbldata.core.utils.descriptions import QUERY_DESCRIPTIONS


class PortfolioQueryParams(QueryParams):
    """
    Query parameters for the PortfolioController.

    This class defines the query parameters used by the PortfolioController.

    Parameters
    ----------
    symbol : str or list of str
        The stock symbol(s) to query. Default is "AAPL".
    provider : OBB_EQUITY_PRICE_HISTORICAL_PROVIDERS
        The data provider for historical price data. Default is "yahoo".
    membership : Literal["anonymous", "humblPEON", "humblPREMIUM", "humblPOWER", "humblPERMANENT", "admin"]
        The membership level of the user accessing the data. Default is "anonymous".

    Attributes
    ----------
    symbol : str or list of str
        The stock symbol(s) to query.
    provider : OBB_EQUITY_PRICE_HISTORICAL_PROVIDERS
        The data provider for historical price data.
    membership : Literal["anonymous", "humblPEON", "humblPREMIUM", "humblPOWER", "humblPERMANENT", "admin"]
        The membership level of the user.
    """

    symbols: str | list[str] = Field(
        default=["AAPL"],
        title="Symbols",
        description=QUERY_DESCRIPTIONS.get("symbols", ""),
    )
    provider: OBB_EQUITY_PRICE_HISTORICAL_PROVIDERS = Field(
        default="yfinance",
        title="Provider",
        description=QUERY_DESCRIPTIONS.get("provider", ""),
    )
    membership: Literal[
        "anonymous",
        "humblPEON",
        "humblPREMIUM",
        "humblPOWER",
        "humblPERMANENT",
        "admin",
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


class PortfolioData(Data):
    """
    The Data for the PortfolioController.
    """

    # Add your data model fields here
    pass
