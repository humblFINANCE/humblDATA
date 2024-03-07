"""
Context: Toolbox || Category: Technical || Sub-Category: MandelBrot Channel || **Sub-Category: Helpers**.

These `Toolbox()` helpers are used in various calculations in the toolbox
context. Most of the helpers will be mathematical transformations of data. These
functions should be **DUMB** functions.
"""

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
        The name of the column to apply volatility bucketing. Default is "realized_volatility".

    Returns
    -------
    pl.LazyFrame
        The `data` with an additional column: `vol_bucket`
    """
    _check_required_columns(data, _column_name_volatility, "symbol")

    result = data.lazy().with_columns(
        pl.col(_column_name_volatility)
        .qcut(
            [lo_quantile, hi_quantile],
            labels=["low", "mid", "high"],
            left_closed=False,
        )
        .over("symbol")
        .alias("vol_bucket")
    )

    return result


def vol_filter(
    data: pl.DataFrame | pl.LazyFrame,
) -> pl.LazyFrame:
    """
    Context: Toolbox || Category: MandelBrot Channel || Sub-Category: Helpers || Command: **vol_filter**.

    If `_rv_adjustment` is True, then filter the data to only include rows
    that are in the same vol_bucket as the latest row for each symbol.
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


def _modify_mandelbrot_prices(
    data: pl.DataFrame | pl.LazyFrame,
    price_range_data: pl.DataFrame | pl.LazyFrame,
    _column_name_cum_sum_max: str,
    _column_name_cum_sum_min: str,
) -> pl.DataFrame | pl.LazyFrame:
    """
    Context: Toolbox || Category: MandelBrot Channel || Sub-Category: Helpers || Command: **_modify_mandelbrot_prices**.

    A private function used in `price_range()` to adjust the top and bottom prices of the mandelbrot channel. This adjustment uses the latest cumulative sum of the deviate series.

    Parameters
    ----------
    data : pl.DataFrame | pl.LazyFrame
        Dataframe or LazyFrame containing cum_sum_max and cum_sum_min values.
    price_range_data : pl.DataFrame | pl.LazyFrame
        Dataframe or LazyFrame containing price range data.
    _column_name_cum_sum_max : str
        Column name for cum_sum_max values.
    _column_name_cum_sum_min : str
        Column name for cum_sum_min values.

    Returns
    -------
    pl.DataFrame | pl.LazyFrame
        Dataframe or LazyFrame with columns for symbol, top_price, recent_price, and bottom_price.
    """
    last_cum_sum_values = (
        data.lazy()
        .group_by("symbol")
        .agg(
            [
                pl.col(_column_name_cum_sum_max)
                .last()
                .alias("last_cum_sum_max"),
                pl.col(_column_name_cum_sum_min)
                .last()
                .alias("last_cum_sum_min"),
            ]
        )
    )

    price_range_data = price_range_data.lazy().join(
        last_cum_sum_values, on="symbol", how="left"
    )

    # Calculate modifiers with safe division to avoid ZeroDivisionError
    price_range_data = price_range_data.with_columns(
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
    out = price_range_data.with_columns(
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
    ).select(
        [
            "symbol",
            "bottom_price",
            "recent_price",
            "top_price",
        ]
    )

    return out


def price_range(
    data: pl.LazyFrame | pl.DataFrame,
    rs_data: pl.DataFrame | pl.LazyFrame,
    recent_price_data: pl.DataFrame | pl.LazyFrame,
    _rs_method: str = "RS",
    _detrended_returns: str = "detrended_log_returns",  # Parameterized detrended_returns column
    *,
    _rv_adjustment: bool = False,
    **kwargs,
) -> pl.DataFrame | pl.LazyFrame:
    """
    Calculate the price range based on the specified method.

    Parameters
    ----------
    data : Union[pl.LazyFrame, pl.DataFrame]
        The DataFrame to calculate the price range from.
    _rs_method : str, optional
        Whether to use the fast method, by default True.
    RS : Optional[pl.Series], optional
        The RS series, by default None.
    RS_mean : Optional[float], optional
        The mean of the RS series, by default None.
    RS_max : Optional[float], optional
        The maximum of the RS series, by default None.
    RS_min : Optional[float], optional
        The minimum of the RS series, by default None.
    recent_price : Optional[float], optional
        The recent price, by default None.
    cumdev_max : Optional[pl.DataFrame], optional
        The maximum range, by default None.
    cumdev_min : Optional[pl.DataFrame], optional
        The minimum range, by default None.
    RS_method : str, optional
        The method to calculate the RS, by default "RS".
    _detrended_returns: str, optional
        The column name for detrended returns, by default "detrended_log_returns".
    **kwargs
        Arbitrary keyword arguments.

    Returns
    -------
    Tuple[float, float]
        The top and bottom price.

    Raises
    ------
    ValueError
        If the RS_method is not one of 'RS', 'RS_mean', 'RS_max', 'RS_min'.
    """
    # Check if RS_method is one of the allowed values
    if _rs_method not in RS_METHODS:
        msg = "RS_method must be one of 'RS', 'RS_mean', 'RS_max', 'RS_min'"
        raise HumblDataError(msg)

    sort_cols = _set_sort_cols(data, "symbol", "date")

    if _rv_adjustment:
        # Calculate STD where detrended_returns are in the same rvol_bucket
        std_detrended_returns = (
            data.lazy()
            .sort(sort_cols)
            .group_by("symbol")
            .agg(
                [
                    pl.col(_detrended_returns)
                    .std()
                    .alias(f"std_{_detrended_returns}")
                ]
            )
        )
    else:
        # Calculate STD where detrended_returns are from the latest range for each symbol
        std_detrended_returns = (
            data.filter(
                (pl.col("window_index") == pl.col("window_index").max()).over(
                    "symbol"
                )
            )
            .group_by("symbol")
            .agg(
                [
                    pl.col(_detrended_returns)
                    .std()
                    .alias(f"std_{_detrended_returns}")
                ]
            )
            # get the latest window of data
            .select(pl.col(["symbol", f"std_{_detrended_returns}"]))
        )
    # Merge RS stats with STD of detrended returns and recent price
    price_range = rs_data.join(std_detrended_returns, on="symbol").join(
        recent_price_data.lazy(), on="symbol"
    )

    price_range = price_range.with_columns(
        (
            pl.col(_rs_method)
            * pl.col("std_detrended_log_returns")
            * pl.col("recent_price")
        ).alias("price_range")
    )

    # Relative Position Modifier
    out = _modify_mandelbrot_prices(
        data,
        price_range,
        "cum_sum_max",
        "cum_sum_min",
    )

    return out
