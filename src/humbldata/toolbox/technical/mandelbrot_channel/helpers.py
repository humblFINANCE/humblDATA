"""
Context: Toolbox || Category: Technical || Sub-Category: MandelBrot Channel || **Sub-Category: Helpers**.

These `Toolbox()` helpers are used in various calculations in the toolbox
context. Most of the helpers will be mathematical transformations of data. These
functions should be **DUMB** functions.
"""

from typing import Literal

import polars as pl

from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.toolbox.toolbox_helpers import (
    _check_required_columns,
    _set_over_cols,
    _set_sort_cols,
    _window_format,
    _window_format_monthly,
)


def add_window_index(
    data: pl.LazyFrame | pl.DataFrame, window: str
) -> pl.LazyFrame | pl.DataFrame:
    """
        Context: Toolbox || Category: MandelBrot Channel || Sub-Category: Helpers || Command: **add_window_index**.

    Add a column to the dataframe indicating the window grouping for each row in
    a time series.

    Parameters
    ----------
    data : pl.LazyFrame | pl.DataFrame
        The input data frame or lazy frame to which the window index will be
        added.
    window : str
        The window size as a string, used to determine the grouping of rows into
        windows.

    Returns
    -------
    pl.LazyFrame | pl.DataFrame
        The original data frame or lazy frame with an additional column named
        "window_index" indicating
        the window grouping for each row.

    Notes
    -----
    - This function is essential for calculating the Mandelbrot Channel, where
    the dataset is split into
    numerous 'windows', and statistics are calculated for each window.
    - The function adds a dummy `symbol` column if the data contains only one
    symbol, to avoid errors in the `group_by_dynamic()` function.
    - It is utilized within the `log_mean()` function for window-based
    calculations.

    Examples
    --------
    >>> data = pl.DataFrame({"date": ["2021-01-01", "2021-01-02"], "symbol": ["AAPL", "AAPL"], "value": [1, 2]})
    >>> window = "1d"
    >>> add_window_index(data, window)
    shape: (2, 4)
    ┌────────────┬────────┬───────┬──────────────┐
    │ date       ┆ symbol ┆ value ┆ window_index │
    │ ---        ┆ ---    ┆ ---   ┆ ---          │
    │ date       ┆ str    ┆ i64   ┆ i64          │
    ╞════════════╪════════╪═══════╪══════════════╡
    │ 2021-01-01 ┆ AAPL   ┆ 1     ┆ 0            │
    ├────────────┼────────┼───────┼──────────────┤
    │ 2021-01-02 ┆ AAPL   ┆ 2     ┆ 1            │
    └────────────┴────────┴───────┴──────────────┘
    """

    def _create_monthly_window_index(col: str, k: int = 1):
        year_diff = pl.col(col).last().dt.year() - pl.col(col).dt.year()
        month_diff = pl.col(col).last().dt.month() - pl.col(col).dt.month()
        day_indicator = pl.col(col).dt.day() > pl.col(col).last().dt.day()
        return (12 * year_diff + month_diff - day_indicator) // k

    # Clean the window into stnaardized strings (i.e "1month"/"1 month" = "1mo")
    window = _window_format(window, _return_timedelta=False)  # returns `str`

    if "w" in window or "d" in window:
        msg = "The window cannot include 'd' or 'w', the window needs to be larger than 1 month!"
        raise HumblDataError(msg)

    window_monthly = _window_format_monthly(window)

    # Adding a 'dummy' column if only one symbol is present in data, to avoid
    # errors in the group_by_dynamic() function
    if "symbol" not in data.columns:
        data = data.with_columns(pl.lit("dummy").alias("symbol"))

    data = data.with_columns(
        _create_monthly_window_index(col="date", k=window_monthly)
        .alias("window_index")
        .over("symbol")
    )

    return data


def vol_buckets(
    data: pl.DataFrame | pl.LazyFrame,
    lo_quantile: float = 0.4,
    hi_quantile: float = 0.8,
    _column_name_volatility: str = "realized_volatility",
    *,
    _boundary_group_down: bool = False,
) -> pl.LazyFrame:
    """
    Context: Toolbox || Category: MandelBrot Channel || Sub-Category: Helpers || Command: **vol_buckets**.

    Splitting data observations into 3 volatility buckets: low, mid and high.
    The function does this for each `symbol` present in the data.

    Parameters
    ----------
    data : pl.LazyFrame | pl.DataFrame
        The input dataframe or lazy frame.
    lo_quantile : float
        The lower quantile for bucketing. Default is 0.4.
    hi_quantile : float
        The higher quantile for bucketing. Default is 0.8.
    _column_name_volatility : str
        The name of the column to apply volatility bucketing. Default is
        "realized_volatility".
    _boundary_group_down: bool = False
        If True, then group boundary values down to the lower bucket, using
        `vol_buckets_alt()` If False, then group boundary values up to the
        higher bucket, using the Polars `.qcut()` method.
        Default is False.

    Returns
    -------
    pl.LazyFrame
        The `data` with an additional column: `vol_bucket`
    """
    _check_required_columns(data, _column_name_volatility, "symbol")

    if not _boundary_group_down:
        # Grouping Boundary Values in Higher Bucket
        out = data.lazy().with_columns(
            pl.col(_column_name_volatility)
            .qcut(
                [lo_quantile, hi_quantile],
                labels=["low", "mid", "high"],
                left_closed=False,
            )
            .over("symbol")
            .alias("vol_bucket")
            .cast(pl.Utf8)
        )
    else:
        out = vol_buckets_alt(
            data, lo_quantile, hi_quantile, _column_name_volatility
        )

    return out


def vol_buckets_alt(
    data: pl.DataFrame | pl.LazyFrame,
    lo_quantile: float = 0.4,
    hi_quantile: float = 0.8,
    _column_name_volatility: str = "realized_volatility",
) -> pl.LazyFrame:
    """
    Context: Toolbox || Category: MandelBrot Channel || Sub-Category: Helpers || Command: **vol_buckets_alt**.

    This is an alternative implementation of `vol_buckets()` using expressions,
    and not using `.qcut()`.
    The biggest difference is how the function groups values on the boundaries
    of quantiles. This function groups boundary values down
    Splitting data observations into 3 volatility buckets: low, mid and high.
    The function does this for each `symbol` present in the data.

    Parameters
    ----------
    data : pl.LazyFrame | pl.DataFrame
        The input dataframe or lazy frame.
    lo_quantile : float
        The lower quantile for bucketing. Default is 0.4.
    hi_quantile : float
        The higher quantile for bucketing. Default is 0.8.
    _column_name_volatility : str
        The name of the column to apply volatility bucketing. Default is "realized_volatility".

    Returns
    -------
    pl.LazyFrame
        The `data` with an additional column: `vol_bucket`

    Notes
    -----
    The biggest difference is how the function groups values on the boundaries
    of quantiles. This function __groups boundary values down__ to the lower bucket.
    So, if there is a value that lies on the mid/low border, this function will
    group it with `low`, whereas `vol_buckets()` will group it with `mid`

    This function is also slightly less performant.
    """
    # Calculate low and high quantiles for each symbol
    low_vol = pl.col(_column_name_volatility).quantile(lo_quantile)
    high_vol = pl.col(_column_name_volatility).quantile(hi_quantile)

    # Determine the volatility bucket for each row using expressions
    vol_bucket = (
        pl.when(pl.col(_column_name_volatility) <= low_vol)
        .then(pl.lit("low"))
        .when(pl.col(_column_name_volatility) <= high_vol)
        .then(pl.lit("mid"))
        .otherwise(pl.lit("high"))
        .alias("vol_bucket")
    )

    # Add the volatility bucket column to the data
    out = data.lazy().with_columns(vol_bucket.over("symbol"))

    return out


def vol_filter(
    data: pl.DataFrame | pl.LazyFrame,
) -> pl.LazyFrame:
    """
    Context: Toolbox || Category: MandelBrot Channel || Sub-Category: Helpers || Command: **vol_filter**.

    If `_rv_adjustment` is True, then filter the data to only include rows
    that are in the same vol_bucket as the latest row for each symbol.

    Parameters
    ----------
    data : pl.DataFrame | pl.LazyFrame
        The input dataframe or lazy frame. This should be the output of
        `vol_buckets()` function in `calc_mandelbrot_channel()`.

    Returns
    -------
    pl.LazyFrame
        The data with only observations in the same volatility bucket as the
        most recent data observation
    """
    _check_required_columns(data, "vol_bucket", "symbol")

    data = data.lazy().with_columns(
        pl.col("vol_bucket").last().over("symbol").alias("last_vol_bucket")
    )

    out = data.filter(
        (pl.col("vol_bucket") == pl.col("last_vol_bucket")).over("symbol")
    ).drop("last_vol_bucket")

    return out


RS_METHODS = ["RS", "RS_mean", "RS_max", "RS_min"]


def _price_range_engine(
    data: pl.DataFrame | pl.LazyFrame,
) -> pl.LazyFrame:
    """
    Context: Toolbox || Category: MandelBrot Channel || Sub-Category: Helpers || Command: **_price_range_engine**.

    A private function used in `price_range()` to calculate the price range.
    This adjustment uses the latest cumulative sum of the deviate series.
    Modify Mandelbrot prices by calculating top and bottom modifiers and prices.

    This function takes a DataFrame or LazyFrame, along with column names for
    cumulative sum maximum and minimum.
    It calculates modifiers to adjust the top and bottom prices based on the
    difference between the last cumulative sum maximum and minimum.
    If the difference is zero, a default modifier of 1 is used. The top and
    bottom prices are then calculated and rounded to 4 decimal places.

    Parameters
    ----------
    data : pl.DataFrame | pl.LazyFrame
        The input data containing price and cumulative sum information.

    Returns
    -------
    pl.LazyFrame
        The modified data with calculated top and bottom prices.

    """
    out = (
        data.lazy()
        # Calculate modifiers with safe division to avoid ZeroDivisionError
        .with_columns(
            [
                pl.when(
                    pl.col("last_cum_sum_max") - pl.col("last_cum_sum_min") != 0
                )
                .then(
                    pl.col("last_cum_sum_max")
                    / (pl.col("last_cum_sum_max") - pl.col("last_cum_sum_min"))
                )
                .otherwise(1)
                .alias("top_modifier"),
                pl.when(
                    pl.col("last_cum_sum_max") - pl.col("last_cum_sum_min") != 0
                )
                .then(
                    pl.col("last_cum_sum_min")
                    / (pl.col("last_cum_sum_max") - pl.col("last_cum_sum_min"))
                )
                .otherwise(1)
                .alias("bottom_modifier"),
            ]
        )
        # Calculate top and bottom prices
        .with_columns(
            [
                (
                    pl.col("recent_price")
                    + pl.col("price_range") * pl.col("top_modifier")
                )
                .round(4)
                .alias("top_price"),
                (
                    pl.col("recent_price")
                    + pl.col("price_range") * pl.col("bottom_modifier")
                )
                .round(4)
                .alias("bottom_price"),
            ]
        )
        # Select relevant columns
        .select(
            [
                "date",
                "symbol",
                "bottom_price",
                "recent_price",
                "top_price",
            ]
        )
    )

    return out


def price_range(
    data: pl.LazyFrame | pl.DataFrame,
    recent_price_data: pl.DataFrame | pl.LazyFrame | None = None,
    rs_method: Literal["RS", "RS_mean", "RS_max", "RS_min"] = "RS",
    _detrended_returns: str = "detrended_log_returns",  # Parameterized detrended_returns column
    _column_name_cum_sum_max: str = "cum_sum_max",
    _column_name_cum_sum_min: str = "cum_sum_min",
    *,
    _rv_adjustment: bool = False,
    _sort: bool = True,
    **kwargs,
) -> pl.LazyFrame:
    """
    Context: Toolbox || Category: MandelBrot Channel || Sub-Category: Helpers || Command: **price_range**.

    Calculate the price range for a given dataset using the Mandelbrot method.

    This function computes the price range based on the recent price data,
    cumulative sum max and min, and RS method specified. It supports adjustments
    for real volatility and sorting of the data based on symbols and dates.

    Parameters
    ----------
    data : pl.LazyFrame | pl.DataFrame
        The dataset containing the financial data.
    recent_price_data : pl.DataFrame | pl.LazyFrame | None
        The dataset containing the most recent price data. If None, the most recent prices are extracted from `data`.
    rs_method : Literal["RS", "RS_mean", "RS_max", "RS_min"], default "RS"
        The RS value to use. Must be one of 'RS', 'RS_mean', 'RS_max', 'RS_min'.
        RS is the column that is the Range/STD of the detrended returns.
    _detrended_returns : str, default "detrended_log_returns"
        The column name for detrended returns in `data`
    _column_name_cum_sum_max : str, default "cum_sum_max"
        The column name for cumulative sum max in `data`
    _column_name_cum_sum_min : str, default "cum_sum_min"
        The column name for cumulative sum min in `data`
    _rv_adjustment : bool, default False
        If True, calculated the `std()` for all observations (since they have
        already been filtered by volatility bucket). If False, then calculates
        the `std()` for the most recent `window_index`
        and uses that to adjust the price range.
    _sort : bool, default True
        If True, sorts the data based on symbols and dates.
    **kwargs
        Arbitrary keyword arguments.

    Returns
    -------
    pl.LazyFrame
        The dataset with calculated price range, including columns for top and
        bottom prices.

    Raises
    ------
    HumblDataError
        If the RS method specified is not supported.

    Examples
    --------
    >>> price_range_data = price_range(data, recent_price_data=None, _rs_method="RS")
    >>> print(price_range_data.columns)
    ['symbol', 'bottom_price', 'recent_price', 'top_price']

    Notes
    -----
    For `rs_method`, you should know how this affects the mandelbrot channel
    that is produced. Selecting RS uses the most recent RS value to calculate
    the price range, whereas selecting RS_mean, RS_max, or RS_min uses the mean,
    max, or min of the RS values, respectively.
    """
    # Check if RS_method is one of the allowed values
    if rs_method not in RS_METHODS:
        msg = "RS_method must be one of 'RS', 'RS_mean', 'RS_max', 'RS_min'"
        raise HumblDataError(msg)

    if isinstance(data, pl.DataFrame):
        data = data.lazy()

    sort_cols = _set_sort_cols(data, "symbol", "date")
    if _sort:
        data.sort(sort_cols)

    # Define Polars Expressions ================================================
    last_cum_sum_max = (
        pl.col(_column_name_cum_sum_max).last().alias("last_cum_sum_max")
    )
    last_cum_sum_min = (
        pl.col(_column_name_cum_sum_min).last().alias("last_cum_sum_min")
    )
    # Define a conditional expression for std_detrended_returns based on _rv_adjustment
    std_detrended_returns_expr = (
        pl.col(_detrended_returns).std().alias(f"std_{_detrended_returns}")
        if _rv_adjustment
        else pl.col(_detrended_returns)
        .filter(pl.col("window_index") == pl.col("window_index").min())
        .std()
        .alias(f"std_{_detrended_returns}")
    )
    date_expr = pl.col("date").max()
    # ===========================================================================

    if rs_method == "RS":
        rs_expr = pl.col("RS").last().alias("RS")
    elif rs_method == "RS_mean":
        rs_expr = pl.col("RS").mean().alias("RS_mean")
    elif rs_method == "RS_max":
        rs_expr = pl.col("RS").max().alias("RS_max")
    elif rs_method == "RS_min":
        rs_expr = pl.col("RS").min().alias("RS_min")

    if recent_price_data is None:
        # if no recent_prices_data is passed, then pull the most recent prices from the data
        recent_price_expr = pl.col("close").last().alias("recent_price")
        # Perform a single group_by operation to calculate both STD of detrended returns and RS statistics
        price_range_data = (
            data.group_by("symbol")
            .agg(
                [
                    date_expr,
                    # Conditional STD calculation based on _rv_adjustment
                    std_detrended_returns_expr,
                    # Recent Price Data
                    recent_price_expr,
                    # cum_sum_max/min last
                    last_cum_sum_max,
                    last_cum_sum_min,
                    # RS statistics
                    rs_expr,
                ]
            )
            # Join with recent_price_data on symbol
            .with_columns(
                (
                    pl.col(rs_method)
                    * pl.col("std_detrended_log_returns")
                    * pl.col("recent_price")
                ).alias("price_range")
            )
            .sort("symbol")
        )
    else:
        price_range_data = (
            data.group_by("symbol")
            .agg(
                [
                    date_expr,
                    # Conditional STD calculation based on _rv_adjustment
                    std_detrended_returns_expr,
                    # cum_sum_max/min last
                    last_cum_sum_max,
                    last_cum_sum_min,
                    # RS statistics
                    rs_expr,
                ]
            )
            # Join with recent_price_data on symbol
            .join(recent_price_data.lazy(), on="symbol")
            .with_columns(
                (
                    pl.col(rs_method)
                    * pl.col("std_detrended_log_returns")
                    * pl.col("recent_price")
                ).alias("price_range")
            )
            .sort("symbol")
        )
    # Relative Position Modifier
    out = _price_range_engine(price_range_data)

    return out
