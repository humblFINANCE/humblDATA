"""
**Context: Portfolio || Category: Analytics || Command: user_table**.

The UserTable Helpers Module.
"""

import asyncio
from datetime import datetime, timedelta
import pytz

import polars as pl

from humbldata.core.utils.openbb_helpers import (
    aget_latest_price,
    aget_sector,
)
from humbldata.toolbox.toolbox_controller import Toolbox


async def user_table_toolbox_generation(symbol: str, user_role: str) -> Toolbox:
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


async def aggregate_user_table_data(symbols: str | list[str] | pl.Series):
    # Fetch data from all sources concurrently
    tasks = [
        aget_latest_price(symbol=symbols),
        aget_sector(symbols=symbols),
        fetch_data_source_3(),
    ]
    results = await asyncio.gather(*tasks)

    # Combine all DataFrames into a single LazyFrame
    combined_df = pl.concat(results, how="vertical").lazy()
    return combined_df
