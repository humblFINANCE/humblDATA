"""
**Context: Portfolio || Category: Analytics || Command: user_table**.

The UserTable Helpers Module.
"""

import asyncio
from datetime import datetime, timedelta

import polars as pl

from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.core.utils.constants import (
    EQUITY_SECTOR_MAPPING,
    EQUITY_SECTORS,
    OBB_EQUITY_PROFILE_PROVIDERS,
)
from humbldata.core.utils.openbb_helpers import (
    aget_equity_sector,
    aget_etf_sector,
    aget_latest_price,
)
from humbldata.toolbox.toolbox_controller import Toolbox


def normalize_sector(sector: str) -> EQUITY_SECTORS:
    """
    Normalize the given sector to a standard EQUITY_SECTORS value.

    Parameters
    ----------
    sector : str
        The sector to normalize.

    Returns
    -------
    EQUITY_SECTORS
        The normalized sector.

    Raises
    ------
    ValueError
        If the sector cannot be normalized to a known EQUITY_SECTORS value.
    """
    normalized = EQUITY_SECTOR_MAPPING.get(sector)
    if normalized is None:
        msg = f"Unknown sector: '{sector}'. Valid sectors are: {', '.join(set(EQUITY_SECTOR_MAPPING.values()))}"
        raise HumblDataError(msg)
    return normalized


async def generate_user_table_toolbox(symbol: str, user_role: str) -> Toolbox:
    """
    Generate a Toolbox instance based on the user's role.

    Parameters
    ----------
    symbol : str
        The stock symbol for the Toolbox.
    user_role : str
        The user's role (anonymous, basic, premium, or power).

    Returns
    -------
    Toolbox
        A Toolbox instance with appropriate date range based on user role.
    """
    end_date = datetime.now().date()

    start_date_mapping = {
        "anonymous": end_date - timedelta(days=365),
        "peon": end_date - timedelta(days=730),
        "premium": end_date - timedelta(days=1825),
        "power": end_date - timedelta(days=7300),
        "permanent": end_date - timedelta(days=7300),
    }

    start_date = start_date_mapping.get(
        user_role.lower(), end_date - timedelta(days=365)
    )
    return Toolbox(
        symbol=symbol,
        interval="1d",
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
    )


async def aget_sector_filter(
    symbols: str | list[str] | pl.Series,
    provider: OBB_EQUITY_PROFILE_PROVIDERS | None = "yfinance",
) -> pl.LazyFrame:
    """
    Context: Portfolio || Category: Analytics || Command: User Table || **Command: aget_sector_filter**.

    Retrieves sector information for given symbols, filling in ETF categories for symbols without sectors.

    Parameters
    ----------
    symbols : str | list[str] | pl.Series
        The symbols to query for sector/category information.
    provider : OBB_EQUITY_PROFILE_PROVIDERS | None, optional
        The data provider to use. Default is "yfinance".

    Returns
    -------
    pl.LazyFrame
        A Polars LazyFrame with columns for symbols and their corresponding sectors/categories.

    Notes
    -----
    This function uses aget_equity_sector() to fetch sector information and aget_etf_category()
    for symbols without sectors. It then combines the results.
    """
    # Get sector information
    equity_sectors = await aget_equity_sector(symbols, provider="yfinance")

    # Identify symbols with null sectors
    etf_symbols = (
        equity_sectors.filter(pl.col("sector").is_null())
        .select(["symbol"])
        .collect()
        .to_series()
        .to_list()
    )
    equity_sectors = equity_sectors.filter(pl.col("sector").is_not_null())

    # Get ETF categories for symbols with null sectors
    if etf_symbols:
        etf_sectors = await aget_etf_sector(etf_symbols, provider="yfinance")

        # Combine sector and ETF information
        etf_sectors = etf_sectors.with_columns(
            pl.col("sector").replace(EQUITY_SECTOR_MAPPING)
        )

        # If all symbols are ETFs, return the ETF sectors (no need to combine)
        if etf_symbols == symbols:
            out_sectors = etf_sectors
        else:
            out_sectors = pl.concat(
                [equity_sectors, etf_sectors], how="vertical"
            )
    else:
        out_sectors = equity_sectors

    return out_sectors


async def aggregate_user_table_data(symbols: str | list[str] | pl.Series):
    # Fetch data from all sources concurrently
    tasks = [
        aget_latest_price(symbol=symbols),
        aget_sector_filter(symbols=symbols),
    ]
    lazyframes = await asyncio.gather(*tasks)

    # Combine all DataFrames into a single LazyFrame
    out = pl.concat(lazyframes, how="align").lazy()
    return out
