"""
**Context: Portfolio || Category: Analytics || Command: user_table**.

The UserTable Helpers Module.
"""

import asyncio
from datetime import datetime, timedelta

import polars as pl

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


async def generate_user_table_toolbox(
    symbols: str | list[str], user_role: str
) -> Toolbox:
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
        symbols=symbols,
        interval="1d",
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
    )


async def aget_sector_filter(
    symbols: str | list[str] | pl.Series,
    provider: OBB_EQUITY_PROFILE_PROVIDERS | None = "yfinance",
    etf_data: ETFCategoryData | None = None,
) -> pl.LazyFrame:
    """
    Context: Portfolio || Category: Analytics || Command: User Table || **Command: aget_sector_filter**.

    Retrieves sector information for given symbols, filling in the ETF sector
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
        equity_sectors.filter(pl.col("sector").is_null())
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
            etf_data = etf_data.filter(pl.col("category").is_not_null())
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
    Context: Portfolio || Category: Analytics || Command: User Table || **Command: aget_asset_class_filter**.

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
    out = out.with_columns(
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
    output_col: str = "ud_pct",
    ratio_col: str = "ud_ratio",
) -> pl.LazyFrame:
    """
    Calculate the up and down percentages for price movements and express them as a ratio.

    This function computes the percentage change from the recent price to the bottom price,
    and from the recent price to the top price. The results are combined into a single string
    column, and the ratio is provided in a separate column.

    Parameters
    ----------
    df : pl.DataFrame
        Input DataFrame containing price data.
    recent_price_col : str, optional
        Name of the column containing recent prices. Default is "recent_price".
    bottom_price_col : str, optional
        Name of the column containing bottom prices. Default is "bottom_price".
    top_price_col : str, optional
        Name of the column containing top prices. Default is "top_price".
    output_col : str, optional
        Name of the output column for price percentages. Default is "price_percentages".
    ratio_col : str, optional
        Name of the output column for the up/down ratio. Default is "ud_ratio".

    Returns
    -------
    pl.DataFrame
        DataFrame with additional columns containing the calculated price percentages and ratio.

    Notes
    -----
    The output column will contain strings in the format "-X.XX / +Y.YY", where X.XX is the
    percentage decrease from recent to bottom price, and Y.YY is the percentage increase from
    recent to top price. The ratio column will contain the ratio of these two percentages.
    """
    return data.with_columns(
        [
            (
                "-"
                + (
                    (pl.col(recent_price_col) - pl.col(bottom_price_col))
                    / pl.col(recent_price_col)
                    * 100
                )
                .abs()
                .round(2)
                .cast(pl.Utf8)
                + " / +"
                + (
                    (pl.col(top_price_col) - pl.col(recent_price_col))
                    / pl.col(recent_price_col)
                    * 100
                )
                .round(2)
                .cast(pl.Utf8)
            ).alias(output_col),
            (
                (pl.col(recent_price_col) - pl.col(bottom_price_col))
                / (pl.col(top_price_col) - pl.col(recent_price_col))
            )
            .round(2)
            .alias(ratio_col),
        ]
    )


async def aggregate_user_table_data(
    symbols: str | list[str] | pl.Series,
    etf_data: pl.LazyFrame | None = None,
    toolbox: Toolbox | None = None,
    mandelbrot_data: pl.LazyFrame | None = None,
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
        # Generate toolbox params based on user_role if not provided
        if toolbox is None:
            toolbox = await generate_user_table_toolbox(
                symbols=symbols, user_role="anonymous"
            )
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
