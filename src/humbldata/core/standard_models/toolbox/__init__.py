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
from typing import List, Optional, Set, Union

from pydantic import Field, field_validator

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.utils.descriptions import QUERY_DESCRIPTIONS


class ToolboxQueryParams(QueryParams):
    """
    Query parameters for the ToolboxController.

    This class defines the query parameters used by the ToolboxController,
    including the stock symbol, data interval, start date, and end date. It also
    includes a method to ensure the stock symbol is in uppercase.

    Attributes
    ----------
    symbol : str
        The symbol or ticker of the stock.
    interval : Optional[str]
        The interval of the data. Defaults to '1d'. Can be None.
    start_date : str
        The start date for the data query.
    end_date : str
        The end date for the data query.

    Methods
    -------
    upper_symbol(cls, v: Union[str, list[str], set[str]]) -> Union[str, list[str]]
        A Pydantic `@field_validator()` that converts the stock symbol to
        uppercase. If a list or set of symbols is provided, each symbol in the
        collection is converted to uppercase and returned as a comma-separated
        string.
    """

    symbol: str = Field(
        default="",
        title="The symbol/ticker of the stock",
        description=QUERY_DESCRIPTIONS.get("symbol", ""),
    )
    interval: str | None = Field(
        default="1d",
        title="The interval of the data",
        description=QUERY_DESCRIPTIONS.get("interval", ""),
    )
    start_date: str = Field(
        default="",
        title="The start date of the data",
        description="The starting date for the data query.",
    )
    end_date: str = Field(
        default="",
        title="The end date of the data",
        description="The ending date for the data query.",
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
        if isinstance(v, str):
            return v.upper()
        return ",".join([symbol.upper() for symbol in list(v)])


class ToolboxData(Data):
    """
    The Data for the ToolboxController.

    WIP: I'm thinking that this is the final layer around which the
    HumblDataObject will be returned to the user, with all necessary information
    about the query, command, data and charts that they should want.
    This HumblDataObject will return values in json/dict format, with methods
    to allow transformation into polars_df, pandas_df, a list, a dict...
    """
