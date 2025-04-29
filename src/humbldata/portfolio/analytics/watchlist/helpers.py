"""
**Context: Portfolio || Category: Analytics || Command: watchlist_table**.

The Watchlist Table Helpers Module.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Literal

import polars as pl
import uvloop

from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.core.standard_models.portfolio.analytics.etf_category import (
    ETFCategoryData,
)
from humbldata.core.utils.constants import (
    GICS_SECTOR_MAPPING,
    GICS_SECTORS,
    OBB_EQUITY_PROFILE_PROVIDERS,
    OBB_ETF_INFO_PROVIDERS,
)
from humbldata.core.utils.openbb_helpers import (
    aget_equity_sector,
    aget_etf_category,
    aget_latest_price,
)
from humbldata.toolbox.toolbox_controller import Toolbox

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def aget_sector_filter(
    symbols: str | list[str] | pl.Series,
    provider: OBB_EQUITY_PROFILE_PROVIDERS | None = "yfinance",
    etf_data: ETFCategoryData | None = None,
) -> pl.LazyFrame:
    """
    Context: Portfolio || Category: Analytics || Command: Watchlist Table || **Command: aget_sector_filter**.

    Retrieves equity sector information for given symbols, filling in the ETF sector
    with the `obb.etf.info` category column from `aget_etf_sector`. This function
    also normalizes the sector to GICS_SECTORS via the
    `.replace(GICS_SECTOR_MAPPING)` method, and renames the `category` column to
    `sector`. The normalization is different from the normalization in
    `aget_asset_class_filter` in that this function uses `.str.replace()` to
    normalize the sector, while `aget_asset_class_filter` uses `.replace()`.
    Using `.str.replace()` allows for Regex matching, but this method since all
    values are known is slightly more performant.

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
        equity_sectors.lazy()
        .filter(pl.col("sector").is_null())
        .select(["symbol"])
        .collect()
        .to_series()
        .to_list()
    )
    equity_sectors = equity_sectors.filter(pl.col("sector").is_not_null())

    # Get ETF categories for symbols with null sectors
    if etf_symbols:
        if etf_data is None:
            etf_categories = await aget_etf_category(
                etf_symbols, provider="yfinance"
            )
        else:
            # Remove columns with NULL (incoming equity symbols from ETF_DATA)
            # since only etf symbols are collected from logic above
            # Validation
            etf_data = etf_data.filter(pl.col("symbol").is_in(etf_symbols))
            etf_categories = ETFCategoryData(etf_data)

        # Normalize Sectors to GICS_SECTORS
        etf_categories = etf_categories.rename(
            {"category": "sector"}
        ).with_columns(pl.col("sector").replace(GICS_SECTOR_MAPPING))

        # If all symbols are ETFs, return the ETF sectors (no need to combine)
        if etf_symbols == symbols:
            out_sectors = etf_categories
        else:
            out_sectors = pl.concat(
                [equity_sectors, etf_categories], how="vertical"
            )
    else:
        out_sectors = equity_sectors

    return out_sectors


def normalize_asset_class(data: pl.LazyFrame) -> pl.LazyFrame:
    """
    Normalize the asset class in the given LazyFrame to standard ASSET_CLASSES values.

    This function uses string replacement to standardize asset class names in
    the 'category' column of the input LazyFrame.

    Parameters
    ----------
    data : pl.LazyFrame
        The input LazyFrame containing 'symbol' and 'category' columns to be normalized.

    Returns
    -------
    pl.LazyFrame
        A new LazyFrame with the 'category' column normalized to standard asset classes.

    Notes
    -----
    This function assumes that the input LazyFrame has 'symbol' and 'category' columns.
    If these columns don't exist, the function may raise an error.
    """
    out = data.with_columns(
        pl.when(pl.col("symbol").is_in(["GLD", "FGDL", "BGLD"]))
        .then(pl.lit("Foreign Exchange"))
        .when(pl.col("symbol").is_in(["UUP", "UDN", "USDU"]))
        .then(pl.lit("Cash"))
        .when(pl.col("symbol").is_in(["BITI", "ETHU", "ZZZ"]))
        .then(pl.lit("Crypto"))
        .when(pl.col("symbol").is_in(["BDRY", "LNGG", "AMPD", "USOY"]))
        .then(pl.lit("Commodity"))
        .otherwise(
            pl.col("category")
            .str.replace(
                r"^(?:\w+\s){0,2}\w*\bBond\b\w*(?:\s\w+){0,2}$", "Fixed Income"
            )
            .str.replace(r".*Commodities.*", "Commodity")
            .str.replace(r".*Digital.*", "Crypto")
            .str.replace(r".*Currency.*", "Foreign Exchange")
            .str.replace(r".*Equity.*", "Equity")
            .str.replace("Utilities", "Equity")
            .str.replace("Financial", "Equity")
            .str.replace("Technology", "Equity")
        )
        .alias("category")
    )
    return out


async def aget_asset_class_filter(
    symbols: str | list[str] | pl.Series,
    provider: OBB_ETF_INFO_PROVIDERS | None = "yfinance",
    etf_data: ETFCategoryData | None = None,
) -> pl.LazyFrame:
    """
    Context: Portfolio || Category: Analytics || Command: Watchlist Table || **Command: aget_asset_class_filter**.

    This function takes in a list of symbols and returns a LazyFrame with the
    asset class for each symbol. Unlike aget_sector_filter, this function
    normalizes the asset class using the normalize_asset_class() method, which
    employs `.str.replace()` for Regex matching. This approach allows for more
    flexible pattern matching but may be slightly less performant than the
    direct `.replace()` method used in aget_sector_filter.

    The function also renames the 'category' column to 'asset_class'. The
    normalization process maps the asset classes to standard ASSET_CLASSES values.
    """
    if etf_data is None:
        out = await aget_etf_category(symbols, provider=provider)
    else:
        out = ETFCategoryData(etf_data)
    out = out.lazy().with_columns(
        [
            pl.when(pl.col("category").is_null())
            .then(pl.lit("Equity"))
            .otherwise(pl.col("category"))
            .alias("category")
        ]
    )
    return out.pipe(normalize_asset_class).rename({"category": "asset_class"})


def calc_up_down_pct(
    data: pl.LazyFrame,
    recent_price_col: str = "recent_price",
    bottom_price_col: str = "bottom_price",
    top_price_col: str = "top_price",
    pct_output_col: str = "ud_pct",
    ratio_output_col: str = "ud_ratio",
) -> pl.LazyFrame:
    """
    Calculate the difference between recent and bottom prices, and recent and top prices, and express the ratio of the two.

    This function computes the percentage change from the recent price to the bottom price,
    and from the recent price to the top price. The results are combined into a single string
    column, and the ratio is provided in a separate column normalized between 0 and 1.

    Parameters
    ----------
    data : pl.DataFrame
        Input DataFrame containing price data.
    recent_price_col : str, optional
        Name of the column containing recent prices. Default is "recent_price".
    bottom_price_col : str, optional
        Name of the column containing bottom prices. Default is "bottom_price".
    top_price_col : str, optional
        Name of the column containing top prices. Default is "top_price".
    pct_output_col : str, optional
        Name of the output column for price percentages. Default is "price_percentages".
    ratio_output_col : str, optional
        Name of the output column for the up/down ratio. Default is "ud_ratio".

    Returns
    -------
    pl.DataFrame
        DataFrame with additional columns containing the calculated price percentages and normalized ratio.

    Notes
    -----
    The output column will contain strings in the format "-X.XX / +Y.YY", where X.XX is the
    percentage decrease from recent to bottom price, and Y.YY is the percentage increase from
    recent to top price. The ratio column will contain a normalized value between 0 and 1,
    where values closer to 1 indicate a better upside/downside ratio.
    """
    return data.with_columns(
        [
            (
                pl.concat_str(
                    [
                        pl.lit("-"),
                        (
                            (
                                pl.col(recent_price_col)
                                - pl.col(bottom_price_col)
                            )
                            / pl.col(recent_price_col)
                            * 100
                        )
                        .abs()
                        .round(2)
                        .cast(pl.Utf8),
                        pl.lit(" / +"),
                        (
                            (pl.col(top_price_col) - pl.col(recent_price_col))
                            / pl.col(recent_price_col)
                            * 100
                        )
                        .round(2)
                        .cast(pl.Utf8),
                    ]
                )
            ).alias(pct_output_col),
            (
                (pl.col(top_price_col) - pl.col(recent_price_col)).abs()
                / (
                    (pl.col(top_price_col) - pl.col(recent_price_col)).abs()
                    + (
                        pl.col(recent_price_col) - pl.col(bottom_price_col)
                    ).abs()
                )
            )
            .round(2)
            .alias(ratio_output_col),
        ]
    )
