"""
Core Module - OpenBB Helpers.

This module contains functions used to interact with OpenBB, or wrap commands
to have specific data outputs.
"""

import asyncio
import warnings

import polars as pl
import uvloop

from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.core.standard_models.abstract.warnings import (
    HumblDataWarning,
    collect_warnings,
)
from humbldata.core.standard_models.openbbapi.EquityPriceQuoteQueryParams import (
    EquityPriceQuoteQueryParams,
)
from humbldata.core.standard_models.openbbapi.EquityProfileQueryParams import (
    EquityProfileQueryParams,
)
from humbldata.core.standard_models.openbbapi.EtfInfoQueryParams import (
    EtfInfoQueryParams,
)
from humbldata.core.utils.constants import (
    OBB_EQUITY_PRICE_QUOTE_PROVIDERS,
    OBB_EQUITY_PROFILE_PROVIDERS,
    OBB_ETF_INFO_PROVIDERS,
    US_ETF_SYMBOLS,
)
from humbldata.core.utils.logger import setup_logger
from humbldata.core.utils.openbb_api_client import OpenBBAPIClient

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


logger = setup_logger("openbb_helpers")


def obb_login(pat: str | None = None) -> bool:
    """
    Log into the OpenBB Hub using a Personal Access Token (PAT).
    (DISABLED: direct obb usage removed)
    """
    warnings.warn(
        "obb_login is deprecated: direct obb usage removed in favor of API client.",
        category=HumblDataWarning,
        stacklevel=1,
    )
    return False


async def aget_latest_price(
    symbols: str | list[str] | pl.Series,
    provider: OBB_EQUITY_PRICE_QUOTE_PROVIDERS = "yfinance",
) -> pl.LazyFrame:
    """
    Asynchronous version of get_latest_price.

    Context: Core || Category: Utils || Subcategory: OpenBB Helpers || **Command: aget_latest_price**.

    Queries the latest stock price data for the given symbol(s) using the
    specified provider asynchronously. This functions collects the latest prices
    for ETF's and Equities, but not futures or options. Defaults to YahooFinance
    (`yfinance`) if no provider is specified. Returns a LazyFrame with the stock
    symbols and their latest prices.

    Parameters
    ----------
    symbols : str | List[str] | pl.Series
        The stock symbol(s) to query for the latest price. Accepts a single
        symbol, a list of symbols, or a Polars Series of symbols.
        You can pass multiple symbols as a string; `'AAPL,XLE'`, and it will
        split the string into a list of symbols.
    provider : OBB_EQUITY_PRICE_QUOTE_PROVIDERS, optional
        The data provider for fetching stock prices. Default is `yfinance`.

    Returns
    -------
    pl.LazyFrame
        A Polars LazyFrame with columns for the stock symbols ('symbol') and
        their latest prices ('recent_price').

    Notes
    -----
    If entering symbols as a string, DO NOT include spaces between the symbols.
    """
    # Normalize symbols to list[str] or str
    if isinstance(symbols, pl.Series):
        symbols = symbols.to_list()
    # Only allow supported providers for the API endpoint
    allowed_providers = {"fmp", "intrinio", "yfinance"}
    provider_literal = provider if provider in allowed_providers else None
    # Build QueryParams
    api_query_params = EquityPriceQuoteQueryParams(
        symbol=symbols,
        provider=provider_literal,
    )
    api_client = OpenBBAPIClient()
    api_response = await api_client.fetch_data(
        obb_path="equity.price.quote",
        api_query_params=api_query_params,
    )
    # Convert HumblObject results to LazyFrame
    if api_response.results is not None:
        out = api_response.to_polars(collect=False)
    else:
        out = pl.LazyFrame([])
    # Standardize output: symbol, recent_price
    if {"last_price", "prev_close"}.issubset(out.collect_schema().names()):
        out = out.select(
            [
                pl.when(pl.col("asset_type") == "ETF")
                .then(pl.col("prev_close"))
                .otherwise(pl.col("last_price"))
                .alias("last_price"),
                pl.col("symbol"),
            ]
        )
    elif "last_price" not in out.collect_schema().names():
        out = out.select(
            pl.col("symbol"), pl.col("prev_close").alias("last_price")
        )
    else:
        out = out.select(pl.col("symbol"), pl.col("last_price"))

    return out


async def aget_last_close(
    symbols: str | list[str] | pl.Series,
    provider: OBB_EQUITY_PRICE_QUOTE_PROVIDERS = "yfinance",
) -> pl.LazyFrame:
    """
    Context: Core || Category: Utils || Subcategory: OpenBB Helpers || **Command: aget_last_close**.

    Asynchronously retrieves the last closing price for the given stock symbol(s) using OpenBB's equity price quote data.

    Parameters
    ----------
    symbols : str | List[str] | pl.Series
        The stock symbol(s) to query for the last closing price. Accepts a single
        symbol, a list of symbols, or a Polars Series of symbols. You can pass
        multiple symbols as a string; `'AAPL,XLE'`, and it will split the string
        into a list of symbols.
    provider : OBB_EQUITY_PRICE_QUOTE_PROVIDERS, optional
        The data provider for fetching stock prices. Default is `yfinance`.

    Returns
    -------
    pl.LazyFrame
        A Polars LazyFrame with columns for the stock symbols ('symbol') and
        their last closing prices ('prev_close').

    Notes
    -----
    This function uses OpenBB's equity price quote data to fetch the last closing price.
    It returns a lazy frame for efficient processing, especially with large datasets.

    If entering symbols as a string, DO NOT include spaces between the symbols.
    """
    # Normalize symbols to list[str] or str
    if isinstance(symbols, pl.Series):
        symbols = symbols.to_list()
    allowed_providers = {"fmp", "intrinio", "yfinance"}
    provider_literal = provider if provider in allowed_providers else None
    # Build QueryParams
    api_query_params = EquityPriceQuoteQueryParams(
        symbol=symbols,
        provider=provider_literal,
    )
    api_client = OpenBBAPIClient()
    api_response = await api_client.fetch_data(
        obb_path="equity.price.quote",
        api_query_params=api_query_params,
    )
    # Convert HumblObject results to LazyFrame
    if api_response.results is not None:
        out = api_response.to_polars(collect=False)
    else:
        out = pl.LazyFrame([])
    # Standardize output: symbol, prev_close
    if "prev_close" in out.collect_schema().names():
        out = out.select(pl.col("symbol"), pl.col("prev_close"))
    else:
        warnings.warn(
            "No latest close price found in API response.",
            category=HumblDataWarning,
            stacklevel=2,
        )
        # fallback: just return symbol and None prev_close
        out = out.select(pl.col("symbol")).with_columns(
            [pl.lit(None).alias("prev_close")]
        )
    return out


async def aget_equity_sector(
    symbols: str | list[str] | pl.Series,
    provider: OBB_EQUITY_PROFILE_PROVIDERS | None = "yfinance",
) -> pl.LazyFrame:
    """
    Asynchronous version of get_sector.

    Context: Core || Category: Utils || Subcategory: OpenBB Helpers || **Command: get_sector_async**.

    Retrieves the sector information for the given stock symbol(s) using
    OpenBB's equity profile data asynchronously. If an ETF is passed, it will
    return a NULL sector for the symbol. The sector returned hasn't been
    normalized to GICS_SECTORS, it is the raw OpenBB sector output.
    Sectors are normalized to GICS_SECTORS in the `aet_sector_filter` function.

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
    # Normalize symbols to list[str] or str
    if isinstance(symbols, pl.Series):
        symbols = symbols.to_list()
    # Build QueryParams
    api_query_params = EquityProfileQueryParams(
        symbol=symbols,
        provider=provider,
    )
    api_client = OpenBBAPIClient()
    api_response = await api_client.fetch_data(
        obb_path="equity.profile",
        api_query_params=api_query_params,
    )
    # Convert HumblObject results to LazyFrame
    if api_response.results is not None:
        out = api_response.to_polars(collect=False)
    else:
        out = pl.LazyFrame([])
    # Standardize output: symbol, sector
    if "sector" in out.collect_schema().names():
        out = out.select([pl.col("symbol"), pl.col("sector")])
    else:
        # If an error occurs, return a LazyFrame with symbol and null sector
        if isinstance(symbols, str):
            symbols = [symbols]
        out = pl.LazyFrame(
            {"symbol": symbols, "sector": [None] * len(symbols)}
        ).cast(pl.Utf8)
    return out


async def aget_etf_category(
    symbols: str | list[str] | pl.Series,
    provider: OBB_ETF_INFO_PROVIDERS | None = "yfinance",
) -> pl.LazyFrame:
    """
    Asynchronously retrieves the category information for the given ETF symbol(s).

    This function uses the `obb.etf.info` function and selects the `category`
    column to get the sector information. This function handles EQUITY
    symbols that are not ETF's the same way that `aget_equity_sector` does.
    The sector returned (under the OpenBB column name `category`) hasn't been
    normalized to GICS_SECTORS, it is the raw OpenBB category output.
    Sectors are normalized to GICS_SECTORS in the `aget_sector_filter` function.

    Parameters
    ----------
    symbols : str | list[str] | pl.Series
        The ETF symbol(s) to query for category information.
    provider : OBB_EQUITY_PROFILE_PROVIDERS | None, optional

    Returns
    -------
    pl.LazyFrame
        A Polars LazyFrame with columns for the ETF symbols ('symbol') and
        their corresponding categories ('category').
    """
    # Convert symbols to list format for consistent handling
    if isinstance(symbols, str):
        symbols_list = [symbols]
    elif isinstance(symbols, pl.Series):
        symbols_list = symbols.to_list()
    else:
        symbols_list = symbols

    # Create a set of US_ETF_SYMBOLS for O(1) lookups
    etf_symbols_set = set(US_ETF_SYMBOLS)

    # Filter symbols to only include those in US_ETF_SYMBOLS
    valid_symbols = [
        symbol for symbol in symbols_list if symbol in etf_symbols_set
    ]

    # If no valid symbols, return early with null categories
    if not valid_symbols:
        return pl.LazyFrame(
            {"symbol": symbols_list, "category": [None] * len(symbols_list)}
        ).cast(pl.Utf8)

    # Create a mapping of original symbols to their validity status
    all_symbols_df = pl.LazyFrame({"symbol": symbols_list})

    try:
        # Use API client to fetch ETF info for valid symbols
        api_query_params = EtfInfoQueryParams(
            symbol=valid_symbols,
            provider=provider,
        )
        api_client = OpenBBAPIClient()
        api_response = await api_client.fetch_data(
            obb_path="etf.info",
            api_query_params=api_query_params,
        )
        out = api_response.to_polars(collect=False).select(
            ["symbol", "category"]
        )

        # Left join to include all input symbols, filling missing categories with null
        out = all_symbols_df.join(out, on="symbol", how="left").with_columns(
            [
                pl.when(pl.col("category").is_null())
                .then(None)
                .otherwise(pl.col("category"))
                .alias("category")
            ]
        )
    except HumblDataError:
        return pl.LazyFrame(
            {"symbol": symbols_list, "category": [None] * len(symbols_list)}
        ).cast(pl.Utf8)

    return out
