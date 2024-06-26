"""
Core Module - OpenBB Helpers.

This module contains functions used to interact with OpenBB, or wrap commands
to have specific data outputs.
"""

import asyncio
import logging
import warnings

import dotenv
import polars as pl
from openbb import obb

from humbldata.core.utils.constants import (
    OBB_EQUITY_PRICE_QUOTE_PROVIDERS,
    OBB_EQUITY_PROFILE_PROVIDERS,
    OBB_ETF_INFO_PROVIDERS,
)
from humbldata.core.utils.env import Env


def obb_login(pat: str | None = None) -> bool:
    """
    Log into the OpenBB Hub using a Personal Access Token (PAT).

    This function wraps the `obb.account.login` method to provide a simplified
    interface for logging into OpenBB Hub. It optionally accepts a PAT. If no PAT
    is provided, it attempts to use the PAT stored in the environment variable
    `OBB_PAT`.

    Parameters
    ----------
    pat : str | None, optional
        The personal access token for authentication. If None, the token is
        retrieved from the environment variable `OBB_PAT`. Default is None.

    Returns
    -------
    bool
        True if login is successful, False otherwise.

    Raises
    ------
    HumblDataError
        If an error occurs during the login process.

    Examples
    --------
    >>> # obb_login("your_personal_access_token_here")
    True

    >>> # obb_login()  # Assumes `OBB_PAT` is set in the environment
    True

    """
    if pat is None:
        pat = Env().OBB_PAT
    try:
        obb.account.login(pat=pat, remember_me=True)
        # obb.account.save()

        # dotenv.set_key(dotenv.find_dotenv(), "OBB_LOGGED_IN", "true")

        return True
    except Exception as e:
        from humbldata.core.standard_models.abstract.warnings import (
            HumblDataWarning,
        )

        # dotenv.set_key(dotenv.find_dotenv(), "OBB_LOGGED_IN", "false")

        warnings.warn(
            "An error occurred while logging into OpenBB. Details below:\n"
            + repr(e),
            category=HumblDataWarning,
            stacklevel=1,
        )
        return False


def get_latest_price(
    symbol: str | list[str] | pl.Series,
    provider: OBB_EQUITY_PRICE_QUOTE_PROVIDERS | None = "yfinance",
) -> pl.LazyFrame:
    """
    Context: Core || Category: Utils || Subcategory: OpenBB Helpers || **Command: get_latest_price**.

    Queries the latest stock price data for the given symbol(s) using the
    specified provider. Defaults to YahooFinance (`yfinance`) if no provider is
    specified. Returns a LazyFrame with the stock symbols and their latest prices.

    Parameters
    ----------
    symbol : str | list[str] | pl.Series
        The stock symbol(s) to query for the latest price. Accepts a single
        symbol, a list of symbols, or a Polars Series of symbols.
    provider : OBB_EQUITY_PRICE_QUOTE_PROVIDERS, optional
        The data provider for fetching stock prices. Defaults is `yfinance`,
        in which case a default provider is used.

    Returns
    -------
    pl.LazyFrame
        A Polars LazyFrame with columns for the stock symbols ('symbol') and
        their latest prices ('last_price').
    """
    logging.getLogger("openbb_terminal.stocks.stocks_model").setLevel(
        logging.CRITICAL
    )

    return (
        obb.equity.price.quote(symbol, provider=provider)
        .to_polars()
        .lazy()
        .select(["symbol", "last_price"])
        .rename({"last_price": "recent_price"})
    )


async def aget_latest_price(
    symbol: str | list[str] | pl.Series,
    provider: OBB_EQUITY_PRICE_QUOTE_PROVIDERS | None = "yfinance",
) -> pl.LazyFrame:
    """
    Asynchronous version of get_latest_price.

    Context: Core || Category: Utils || Subcategory: OpenBB Helpers || **Command: get_latest_price_async**.

    Queries the latest stock price data for the given symbol(s) using the
    specified provider asynchronously. Defaults to YahooFinance (`yfinance`) if no provider is
    specified. Returns a LazyFrame with the stock symbols and their latest prices.

    Parameters
    ----------
    symbol : str | List[str] | pl.Series
        The stock symbol(s) to query for the latest price. Accepts a single
        symbol, a list of symbols, or a Polars Series of symbols.
    provider : OBB_EQUITY_PRICE_QUOTE_PROVIDERS, optional
        The data provider for fetching stock prices. Default is `yfinance`.

    Returns
    -------
    pl.LazyFrame
        A Polars LazyFrame with columns for the stock symbols ('symbol') and
        their latest prices ('recent_price').

    Notes
    -----
    If you run into an error: `RuntimeError: asyncio.run() cannot be called from a running event loop`
    you can use the following code to apply the asyncio event loop to the current thread:
    ```
    import nest_asyncio
    nest_asyncio.apply()
    ```
    """
    logging.getLogger("openbb_terminal.stocks.stocks_model").setLevel(
        logging.CRITICAL
    )

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, lambda: obb.equity.price.quote(symbol, provider=provider)
    )

    return (
        result.to_polars()
        .lazy()
        .select(["symbol", "last_price"])
        .rename({"last_price": "recent_price"})
    )


def get_equity_sector(
    symbols: str | list[str] | pl.Series,
    provider: OBB_EQUITY_PROFILE_PROVIDERS | None = "yfinance",
) -> pl.LazyFrame:
    """
    Context: Core || Category: Utils || Subcategory: OpenBB Helpers || **Command: get_sector**.

    Retrieves the sector information for the given stock symbol(s) using OpenBB's equity profile data.

    Parameters
    ----------
    symbols : str | list[str] | pl.Series
        The stock symbol(s) to query for sector information. Accepts a single
        symbol, a list of symbols, or a Polars Series of symbols.
    provider : str | None, optional
        The data provider to use for fetching sector information. If None, the default
        provider will be used.

    Returns
    -------
    pl.LazyFrame
        A Polars LazyFrame with columns for the stock symbols ('symbol') and
        their corresponding sectors ('sector').

    Notes
    -----
    This function uses OpenBB's equity profile data to fetch sector information.
    It returns a lazy frame for efficient processing, especially with large datasets.
    """
    try:
        result = obb.equity.profile(symbols, provider=provider)
        return result.to_polars().select(["symbol", "sector"]).lazy()
    except pl.exceptions.ColumnNotFoundError:
        # If an error occurs, return a LazyFrame with symbol and null sector
        if isinstance(symbols, str):
            symbols = [symbols]
        elif isinstance(symbols, pl.Series):
            symbols = symbols.to_list()
        return pl.LazyFrame(
            {"symbol": symbols, "sector": [None] * len(symbols)}
        )


async def aget_equity_sector(
    symbols: str | list[str] | pl.Series,
    provider: OBB_EQUITY_PROFILE_PROVIDERS | None = "yfinance",
) -> pl.LazyFrame:
    """
    Asynchronous version of get_sector.

    Context: Core || Category: Utils || Subcategory: OpenBB Helpers || **Command: get_sector_async**.

    Retrieves the sector information for the given stock symbol(s) using OpenBB's equity profile data asynchronously.

    Parameters
    ----------
    symbols : str | List[str] | pl.Series
        The stock symbol(s) to query for sector information. Accepts a single
        symbol, a list of symbols, or a Polars Series of symbols.
    provider : str | None, optional
        The data provider to use for fetching sector information. If None, the default
        provider will be used.

    Returns
    -------
    pl.LazyFrame
        A Polars LazyFrame with columns for the stock symbols ('symbol') and
        their corresponding sectors ('sector').

    Notes
    -----
    This function uses OpenBB's equity profile data to fetch sector information.
    It returns a lazy frame for efficient processing, especially with large datasets.
    If you just pass an ETF to the `obb.equity.profile` function, it will throw
    return data without the NULL columns (sector column included) and only
    returns columns where there is data, so we need to handle that edge case.
    If an ETF is included with an equity, it will return a NULL sector column,
    so we can select the sector column from the ETF data and return it as a
    NULL sector for the equity.
    """
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None, lambda: obb.equity.profile(symbols, provider=provider)
        )
        return result.to_polars().select(["symbol", "sector"]).lazy()
    except pl.exceptions.ColumnNotFoundError:
        # If an error occurs, return a LazyFrame with symbol and null sector
        if isinstance(symbols, str):
            symbols = [symbols]
        elif isinstance(symbols, pl.Series):
            symbols = symbols.to_list()
        return pl.LazyFrame(
            {"symbol": symbols, "sector": [None] * len(symbols)}
        )


async def aget_etf_sector(
    symbols: str | list[str] | pl.Series,
    provider: OBB_ETF_INFO_PROVIDERS | None = "yfinance",
) -> pl.LazyFrame:
    """
    Asynchronously retrieves the sector information for the given ETF symbol(s).

    This function uses the `obb.etf.info` function and selects the `category`
    column to get the sector information.

    Parameters
    ----------
    symbols : str | list[str] | pl.Series
        The ETF symbol(s) to query for category information.
    provider : OBB_EQUITY_PROFILE_PROVIDERS | None, optional
        The data provider to use. Default is "yfinance".

    Returns
    -------
    pl.LazyFrame
        A Polars LazyFrame with columns for the ETF symbols ('symbol') and
        their corresponding categories ('category').
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, lambda: obb.etf.info(symbols, provider=provider)
    )

    return (
        result.to_polars()
        .lazy()
        .select(["symbol", "category"])
        .rename({"category": "sector"})
    )
