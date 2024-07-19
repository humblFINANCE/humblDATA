"""
**Context: Portfolio || Category: Analytics || Command: user_table**.

The user_table Command Module.
"""

import asyncio
from typing import Literal

import polars as pl

from humbldata.core.utils.openbb_helpers import (
    aget_etf_category,
    aget_latest_price,
)
from humbldata.portfolio.analytics.user_table.helpers import (
    aget_asset_class_filter,
    aget_sector_filter,
    calc_up_down_pct,
)
from humbldata.toolbox.toolbox_controller import Toolbox


async def user_table_engine(
    symbols: str | list[str] | pl.Series,
    etf_data: pl.LazyFrame | None = None,
    toolbox: Toolbox | None = None,
    mandelbrot_data: pl.LazyFrame | None = None,
    membership: Literal[
        "anonymous", "peon", "premium", "power", "admin"
    ] = "anonymous",
):
    """
    Aggregate user table data from various sources.

    Parameters
    ----------
    symbols : str or list of str or pl.Series
        The stock symbols to aggregate data for.
    etf_data : pl.LazyFrame or None, optional
        Pre-fetched ETF data. If None, it will be fetched, by default None.
    toolbox : Toolbox or None, optional
        Pre-generated toolbox. If None, it will be generated, by default None.
    mandelbrot_data : pl.LazyFrame or None, optional
        Pre-calculated Mandelbrot channel data. If None, it will be calculated, by default None.
    membership : Literal["anonymous", "peon", "premium", "power", "admin"], optional
        The user's role. If None, it will be calculated, by default None.

    Returns
    -------
    pl.LazyFrame
        A LazyFrame containing the aggregated user table data with columns:
        date, symbol, bottom_price, recent_price, top_price, ud_pct, ud_ratio,
        sector, and asset_class.

    Notes
    -----
    This function performs the following steps:
    1. Fetches ETF data if not provided
    2. Generates a toolbox if not provided
    3. Calculates Mandelbrot channel if not provided
    4. Concurrently fetches latest price, sector, and asset class data
    5. Combines all data into a single LazyFrame
    6. Calculates up/down percentages and ratios
    7. Selects and returns relevant columns

    The function uses asynchronous operations for improved performance when
    fetching data from multiple sources.
    """
    # Fetch ETF data if not provided
    if etf_data is None:
        etf_data = await aget_etf_category(symbols=symbols)

    # Calculate Mandelbrot channel if not provided
    if mandelbrot_data is None:
        # Generate toolbox params based on membership if not provided
        if toolbox is None:
            toolbox = Toolbox(symbols=symbols, membership=membership)
        mandelbrot_data = toolbox.technical.mandelbrot_channel().to_polars(
            collect=False
        )
    # Fetch data from all sources concurrently, passing etf_data where needed
    tasks = [
        aget_latest_price(symbols=symbols),
        aget_sector_filter(symbols=symbols, etf_data=etf_data),
        aget_asset_class_filter(symbols=symbols, etf_data=etf_data),
    ]
    lazyframes = await asyncio.gather(*tasks)

    # Combine all DataFrames into a single LazyFrame
    out = (
        (
            pl.concat(lazyframes, how="align")
            .lazy()
            .join(mandelbrot_data, on="symbol", how="left")
            .pipe(calc_up_down_pct)
        )
        .select(
            [
                "date",
                "symbol",
                "bottom_price",
                "recent_price",
                "top_price",
                "ud_pct",
                "ud_ratio",
                "sector",
                "asset_class",
            ]
        )
        .rename({"recent_price": "last_price"})
        .rename({"bottom_price": "buy_price"})
        .rename({"top_price": "sell_price"})
    )
    return out
