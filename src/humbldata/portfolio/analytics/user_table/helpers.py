"""
**Context: Portfolio || Category: Analytics || Command: user_table**.

The UserTable Helpers Module.
"""

import asyncio
from datetime import datetime, timedelta
import pytz

import polars as pl
from humbldata.core.utils.constants import OBB_EQUITY_PROFILE_PROVIDERS

from humbldata.core.utils.openbb_helpers import (
    aget_etf_category,
    aget_latest_price,
    aget_equity_sector,
)
from humbldata.toolbox.toolbox_controller import Toolbox


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
    end_date = datetime.now(tz=pytz.).date()

    start_date_mapping = {
        "anonymous": end_date - timedelta(days=365),
        "basic": end_date - timedelta(days=730),
        "premium": end_date - timedelta(days=1825),
        "power": end_date - timedelta(days=7300),
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
    equity_sectors = await aget_equity_sector(symbols, provider)

    # Identify symbols with null sectors
    null_sector_symbols = equity_sectors.filter(pl.col("issue").is_null()).select(["symbol"]).collect().to_series().to_list()


    # Get ETF categories for symbols with null sectors
    if null_sector_symbols:
        etf_info = await aget_etf_category(null_sector_symbols, provider)

        # Combine sector and ETF information
        combined_info = (
            equity_sectors.filter(pl.col("sector").is_not_null())
            .concat(etf_info.rename({"category": "sector"}))
            .sort("symbol")
        )
    else:
        combined_info = equity_sectors

    return combined_info


async def aggregate_user_table_data(symbols: str | list[str] | pl.Series):
    # Fetch data from all sources concurrently
    tasks = [
        aget_latest_price(symbol=symbols),
        aget_equity_sector(symbols=symbols),
    ]
    results = await asyncio.gather(*tasks)

    # Combine all DataFrames into a single LazyFrame
    combined_df = pl.concat(results, how="vertical").lazy()
    return combined_df
