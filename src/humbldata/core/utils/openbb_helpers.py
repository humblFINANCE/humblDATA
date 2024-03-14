"""
Core Module - OpenBB Helpers.

This module contains functions used to interact with OpenBB, or wrap commands
to have specific data outputs.
"""

import logging
import warnings
from typing import Literal

import dotenv
import polars as pl
from openbb import obb

from humbldata.core.utils.constants import OBB_EQUITY_PRICE_QUOTE_PROVIDERS
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
        .collect()
    )
