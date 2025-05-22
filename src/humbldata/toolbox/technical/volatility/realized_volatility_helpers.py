"""
Context: Toolbox || Category: Technical || **Sub-Category: Volatility Helpers**.

All of the volatility estimators used in `calc_realized_volatility()`.
These are various methods to calculate the realized volatility of financial data.
"""

import math

import numpy as np
import polars as pl

from humbldata.toolbox.toolbox_helpers import (
    _check_required_columns,
    _set_over_cols,
    _set_sort_cols,
    _window_format,
)


def _annual_vol(data: pl.Series, trading_periods: int = 252) -> float:
    """
    Context: Toolbox || Category: Technical || Sub-Category: Volatility Helpers || **Command: _annual_vol**.

    This function calculates the annualized volatility of a given Polars Series
    `data`. It computes the square root of the product of the number of trading
    periods in a year and the mean of the squared returns in the series. This
    is a common approach to annualize the volatility of financial data.

    Parameters
    ----------
    data : pl.Series
        A series of returns from which to calculate the annual volatility.
    trading_periods : int, optional
        The number of trading periods in a year, typically 252 for the stock
        market.

    Returns
    -------
    pl.Series
        The annualized volatility of the input series.

    Notes
    -----
    In the context of volatility estimators like Parkinson, Garman-Klass, and
    Rogers Satchell, this function is pivotal for calculating the annualized
    volatility. The process involves:

    1. Calculating the mean of the series `data`, which represents the average
    daily volatility in the context of daily volatility measures.
    2. Multiplying this mean by the number of trading periods in a year
    (typically 252) to scale the daily volatility to an annual measure.
    3. Taking the square root of this product to obtain the annualized
    volatility, as volatility is conventionally expressed as the standard
    deviation of returns, which is the square root of variance.

    Thus, this function serves to transform daily volatility measures into an
    annualized volatility figure, facilitating comparison across different time
    frames and instruments.
    """
    return (trading_periods * data.mean()) ** 0.5


def std(
    data: pl.DataFrame | pl.LazyFrame | pl.Series,
    window: str = "1m",
    trading_periods=252,
    _drop_nulls: bool = True,
    _avg_trading_days: bool = False,
    _column_name_returns: str = "log_returns",
    _sort: bool = True,
) -> pl.LazyFrame | pl.Series:
    """
    Context: Toolbox || Category: Technical || Sub-Category: Volatility Helpers || **Command: _std**.

    This function computes the standard deviation of returns, which is a common
    measure of volatility.It calculates the rolling standard deviation for a
    given window size, optionally adjusting for the average number of trading
    days and scaling the result to an annualized volatility percentage.

    Parameters
    ----------
    data : Union[pl.DataFrame, pl.LazyFrame, pl.Series]
        The input data containing the returns. It can be a DataFrame, LazyFrame,
        or Series.
    window : str, optional
        The rolling window size for calculating the standard deviation.
        The default is "1m" (one month).
    trading_periods : int, optional
        The number of trading periods in a year, used for annualizing the
        volatility. The default is 252.
    _drop_nulls : bool, optional
        If True, null values will be dropped from the result.
        The default is True.
    _avg_trading_days : bool, optional
        If True, the average number of trading days will be used when
        calculating the window size. The default is True.
    _column_name_returns : str, optional
        The name of the column containing the returns. This parameter is used
        when `data` is a DataFrame or LazyFrame. The default is "log_returns".

    Returns
    -------
    Union[pl.DataFrame, pl.LazyFrame, pl.Series]
        The input data structure with an additional column for the rolling
        standard deviation of returns, or the modified Series with the rolling
        standard deviation values.
    """
    window_timedelta = _window_format(
        window, _return_timedelta=True, _avg_trading_days=_avg_trading_days
    )
    if isinstance(data, pl.Series):
        return data.rolling_std(
            window_size=window_timedelta.days, min_periods=1
        )

    sort_cols = _set_sort_cols(data, "symbol", "date")
    over_cols = _set_over_cols(data, "symbol")  # Get symbol for grouping

    if _sort and sort_cols:
        data = data.lazy().sort(sort_cols)
        for col in sort_cols:
            data = data.set_sorted(col)

    # Calculate std per symbol group using .over()
    result = data.lazy().with_columns(
        (
            pl.col(_column_name_returns)
            .rolling_std_by(
                window_size=window_timedelta,
                min_periods=2,  # using min_periods=2, bc if min_periods=1, the first value will be 0.
                by="date",
            )
            .over(over_cols)  # Apply per symbol group
            * math.sqrt(trading_periods)
            * 100
        ).alias(f"std_volatility_pct_{window_timedelta.days}D")
    )

    if _drop_nulls:
        return result.drop_nulls(
            subset=f"std_volatility_pct_{window_timedelta.days}D"
        )
    return result


def parkinson(
    data: pl.DataFrame | pl.LazyFrame,
    window: str = "1m",
    _column_name_high: str = "high",
    _column_name_low: str = "low",
    *,
    _drop_nulls: bool = True,
    _avg_trading_days: bool = False,
    _sort: bool = True,
) -> pl.LazyFrame:
    """
    Calculate Parkinson's volatility over a specified window.

    Parkinson's volatility is a measure that uses the stock's high and low prices
    of the day rather than just close to close prices. It is particularly useful
    for capturing large price movements during the day.

    Parameters
    ----------
    data : pl.DataFrame | pl.LazyFrame
        The input data containing the stock prices.
    window : int, optional
        The rolling window size for calculating volatility, by default 30.
    trading_periods : int, optional
        The number of trading periods in a year, by default 252.
    _column_name_high : str, optional
        The name of the column containing the high prices, by default "high".
    _column_name_low : str, optional
        The name of the column containing the low prices, by default "low".
    _drop_nulls : bool, optional
        Whether to drop null values from the result, by default True.
    _avg_trading_days : bool, optional
        Whether to use the average number of trading days when calculating the
        window size, by default True.

    Returns
    -------
    pl.DataFrame | pl.LazyFrame
        The calculated Parkinson's volatility, with an additional column
        "parkinson_volatility_pct_{window_int}D"
        indicating the percentage volatility.

    Notes
    -----
    This function requires the input data to have 'high' and 'low' columns to
    calculate
    the logarithm of their ratio, which is squared and scaled by a constant to
    estimate
    volatility. The result is then annualized and expressed as a percentage.

    Usage
    -----
    If you pass `"1m` as a `window` argument and  `_avg_trading_days=False`.
    The result will be `30`. If `_avg_trading_days=True`, the result will be
    `21`.

    Examples
    --------
    >>> data = pl.DataFrame({'high': [120, 125], 'low': [115, 120]})
    >>> _parkinson(data)
    A DataFrame with the calculated Parkinson's volatility.
    """
    sort_cols = _set_sort_cols(data, "symbol", "date")
    over_cols = _set_over_cols(data, "symbol")  # Get symbol for grouping

    if _sort and sort_cols:
        data = data.lazy().sort(sort_cols)
        for col in sort_cols:
            data = data.set_sorted(col)

    window_int: int = _window_format(
        window, _return_timedelta=True, _avg_trading_days=_avg_trading_days
    ).days

    # Keep everything in lazy context and calculate per symbol
    result = (
        data.lazy()
        # Calculate log ratio and square it per symbol
        .with_columns(
            (
                (pl.col(_column_name_high) / pl.col(_column_name_low))
                .log()
                .pow(2)
                * (1.0 / (4.0 * math.log(2.0)))  # var1 constant
            ).alias("rs")
        )
        # Calculate rolling annual volatility per symbol using _annual_vol
        .with_columns(
            (
                pl.col("rs")
                .rolling_map(_annual_vol, window_size=window_int, min_periods=1)
                .over(over_cols)  # Apply per symbol group
                * 100
            ).alias(f"parkinson_volatility_pct_{window_int}D")
        )
        .drop("rs")  # Remove intermediate calculation
    )

    if _drop_nulls:
        return result.drop_nulls(
            subset=f"parkinson_volatility_pct_{window_int}D"
        )

    return result


def garman_klass(
    data: pl.DataFrame | pl.LazyFrame,
    window: str = "1m",
    _column_name_high: str = "high",
    _column_name_low: str = "low",
    _column_name_open: str = "open",
    _column_name_close: str = "close",
    _drop_nulls: bool = True,
    _avg_trading_days: bool = False,
    _sort: bool = True,
) -> pl.LazyFrame:
    """
    Context: Toolbox || Category: Technical || Sub-Category: Volatility Helpers || **Command: _garman_klass**.

    Calculates the Garman-Klass volatility for a given dataset.

    Parameters
    ----------
    data : pl.DataFrame | pl.LazyFrame
        The input data containing the price information.
    window : str, optional
        The rolling window size for volatility calculation, by default "1m".
    _column_name_high : str, optional
        The name of the column containing the high prices, by default "high".
    _column_name_low : str, optional
        The name of the column containing the low prices, by default "low".
    _column_name_open : str, optional
        The name of the column containing the opening prices, by default "open".
    _column_name_close : str, optional
        The name of the column containing the adjusted closing prices, by
        default "close".
    _drop_nulls : bool, optional
        Whether to drop null values from the result, by default True.
    _avg_trading_days : bool, optional
        Whether to use the average number of trading days when calculating the
        window size, by default True.

    Returns
    -------
    pl.DataFrame | pl.LazyFrame | pl.Series
        The calculated Garman-Klass volatility, with an additional column
        "volatility_pct" indicating the percentage volatility.

    Notes
    -----
    Garman-Klass volatility extends Parkinson’s volatility by considering the
    opening and closing prices in addition to the high and low prices. This
    approach provides a more accurate estimation of volatility, especially in
    markets with significant activity at the opening and closing of trading
    sessions.
    """
    sort_cols = _set_sort_cols(data, "symbol", "date")
    over_cols = _set_over_cols(data, "symbol")  # Get symbol for grouping

    if _sort and sort_cols:
        data = data.lazy().sort(sort_cols)
        for col in sort_cols:
            data = data.set_sorted(col)

    window_int: int = _window_format(
        window, _return_timedelta=True, _avg_trading_days=_avg_trading_days
    ).days

    # Keep everything in lazy context and calculate per symbol
    result = (
        data.lazy()
        # Calculate intermediate values per symbol
        .with_columns(
            [
                (pl.col(_column_name_high) / pl.col(_column_name_low))
                .log()
                .pow(2)
                .alias("log_hi_lo_sq"),
                (pl.col(_column_name_close) / pl.col(_column_name_open))
                .log()
                .pow(2)
                .alias("log_close_open_sq"),
            ]
        )
        # Calculate Garman-Klass estimator
        .with_columns(
            (
                0.5 * pl.col("log_hi_lo_sq")
                - (2 * math.log(2) - 1) * pl.col("log_close_open_sq")
            ).alias("rs")
        )
        # Calculate rolling annual volatility per symbol using _annual_vol
        .with_columns(
            (
                pl.col("rs")
                .rolling_map(_annual_vol, window_size=window_int, min_periods=1)
                .over(over_cols)  # Apply per symbol group
                * 100
            ).alias(f"gk_volatility_pct_{window_int}D")
        )
        # Remove intermediate calculations
        .drop(["log_hi_lo_sq", "log_close_open_sq", "rs"])
    )

    if _drop_nulls:
        return result.drop_nulls(subset=f"gk_volatility_pct_{window_int}D")
    return result


def hodges_tompkins(
    data: pl.DataFrame | pl.LazyFrame | pl.Series,
    window: str = "1m",
    trading_periods=252,
    _column_name_returns: str = "log_returns",
    *,
    _drop_nulls: bool = True,
    _avg_trading_days: bool = False,
    _sort: bool = True,
) -> pl.LazyFrame | pl.Series:
    """
    Context: Toolbox || Category: Technical || Sub-Category: Volatility Helpers || **Command: _hodges_tompkins**.

    Hodges-Tompkins volatility is a bias correction for estimation using an
    overlapping data sample that produces unbiased estimates and a
    substantial gain in efficiency.
    """
    # Define Window Size
    window_timedelta = _window_format(
        window, _return_timedelta=True, _avg_trading_days=_avg_trading_days
    )
    h: int = window_timedelta.days

    if isinstance(data, pl.Series):
        vol = data.rolling_std(window_size=h, min_periods=1)
        count = data.len()
        n = (count - h) + 1
        adj_factor = 1.0 / (1.0 - (h / n) + ((h**2 - 1) / (3 * n**2)))
        return (vol * adj_factor) * 100

    sort_cols = _set_sort_cols(data, "symbol", "date")
    over_cols = _set_over_cols(data, "symbol")  # Get symbol for grouping

    if _sort and sort_cols:
        data = data.lazy().sort(sort_cols)
        for col in sort_cols:
            data = data.set_sorted(col)

    # Keep everything in lazy context and calculate per symbol
    result = (
        data.lazy()
        # Calculate count per symbol for adjustment factor
        .with_columns(
            [
                pl.count().over(over_cols).alias("symbol_count"),
                # Calculate std per symbol
                (
                    pl.col(_column_name_returns)
                    .rolling_std_by(
                        window_size=window_timedelta, min_periods=1, by="date"
                    )
                    .over(over_cols)
                    * np.sqrt(trading_periods)
                ).alias("vol"),
            ]
        )
        # Calculate n and adjustment factor per symbol
        .with_columns(((pl.col("symbol_count") - h + 1).alias("n")))
        .with_columns(
            (
                1.0
                / (
                    1.0
                    - (h / pl.col("n"))
                    + ((h**2 - 1) / (3 * pl.col("n").pow(2)))
                )
            ).alias("adj_factor")
        )
        # Calculate final Hodges-Tompkins volatility
        .with_columns(
            (pl.col("vol") * pl.col("adj_factor") * 100).alias(
                f"ht_volatility_pct_{h}D"
            )
        )
        # Remove intermediate calculations
        .drop(["symbol_count", "n", "adj_factor", "vol"])
    )

    if _drop_nulls:
        result = result.drop_nulls(subset=f"ht_volatility_pct_{h}D")
    return result


def rogers_satchell(
    data: pl.DataFrame | pl.LazyFrame,
    window: str = "1m",
    _column_name_high: str = "high",
    _column_name_low: str = "low",
    _column_name_open: str = "open",
    _column_name_close: str = "close",
    _drop_nulls: bool = True,
    _avg_trading_days: bool = False,
    _sort: bool = True,
) -> pl.LazyFrame:
    """
    Context: Toolbox || Category: Technical || Sub-Category: Volatility Helpers || **Command: _rogers_satchell**.

    Rogers-Satchell is an estimator for measuring the volatility of
    securities with an average return not equal to zero. Unlike Parkinson
    and Garman-Klass estimators, Rogers-Satchell incorporates a drift term
    (mean return not equal to zero). This function calculates the
    Rogers-Satchell volatility estimator over a specified window and optionally
    drops null values from the result.

    Parameters
    ----------
    data : pl.DataFrame | pl.LazyFrame
        The input data for which to calculate the Rogers-Satchell volatility
        estimator. This can be either a DataFrame or a LazyFrame. There need to
        be OHLC columns present in the data.
    window : str, default "1m"
        The window over which to calculate the volatility estimator. The
        window is specified as a string, such as "1m" for one month.
    _column_name_high : str, default "high"
        The name of the column representing the high prices in the data.
    _column_name_low : str, default "low"
        The name of the column representing the low prices in the data.
    _column_name_open : str, default "open"
        The name of the column representing the opening prices in the data.
    _column_name_close : str, default "close"
        The name of the column representing the adjusted closing prices in the
        data.
    _drop_nulls : bool, default True
        Whether to drop null values from the result. If True, rows with null
        values in the calculated volatility column will be removed from the
        output.
    _avg_trading_days : bool, default True
        Indicates whether to use the average number of trading days per window.
        This affects how the window size is interpreted. i.e instead of "1mo"
        returning `timedelta(days=31)`, it will return `timedelta(days=21)`.

    Returns
    -------
    pl.DataFrame | pl.LazyFrame
        The input data with an additional column containing the calculated
        Rogers-Satchell volatility estimator. The return type matches the input
        type (DataFrame or LazyFrame).
    """
    # Check if all required columns are present in the DataFrame
    _check_required_columns(
        data,
        _column_name_high,
        _column_name_low,
        _column_name_open,
        _column_name_close,
    )
    sort_cols = _set_sort_cols(data, "symbol", "date")
    over_cols = _set_over_cols(data, "symbol")  # Get symbol for grouping

    if _sort and sort_cols:
        data = data.lazy().sort(sort_cols)
        for col in sort_cols:
            data = data.set_sorted(col)

    window_int: int = _window_format(
        window=window,
        _return_timedelta=True,
        _avg_trading_days=_avg_trading_days,
    ).days

    # Keep everything in lazy context and calculate per symbol
    result = (
        data.lazy()
        # Calculate intermediate log ratios per symbol
        .with_columns(
            [
                (pl.col(_column_name_high) / pl.col(_column_name_open))
                .log()
                .over(over_cols)
                .alias("log_ho"),
                (pl.col(_column_name_low) / pl.col(_column_name_open))
                .log()
                .over(over_cols)
                .alias("log_lo"),
                (pl.col(_column_name_close) / pl.col(_column_name_open))
                .log()
                .over(over_cols)
                .alias("log_co"),
            ]
        )
        # Calculate Rogers-Satchell estimator per symbol
        .with_columns(
            (
                pl.col("log_ho") * (pl.col("log_ho") - pl.col("log_co"))
                + pl.col("log_lo") * (pl.col("log_lo") - pl.col("log_co"))
            )
            .over(over_cols)
            .alias("rs")
        )
        # Calculate rolling annual volatility per symbol
        .with_columns(
            (
                pl.col("rs")
                .rolling_map(_annual_vol, window_size=window_int, min_periods=1)
                .over(over_cols)  # Apply per symbol group
                * 100
            ).alias(f"rs_volatility_pct_{window_int}D")
        )
        # Remove intermediate calculations
        .drop(["log_ho", "log_lo", "log_co", "rs"])
    )

    if _drop_nulls:
        result = result.drop_nulls(subset=f"rs_volatility_pct_{window_int}D")
    return result


def _yang_zhang_engine(
    data: pl.DataFrame | pl.LazyFrame,
    window: int,
    over_cols: list[str] | None,
) -> pl.DataFrame | pl.LazyFrame:
    """Calculate Yang-Zhang components per symbol group."""
    _check_required_columns(data, "log_cc_sq", "log_oc_sq", "rs")

    out = data.lazy().with_columns(
        [
            (
                pl.col("log_cc_sq")
                .rolling_sum(window_size=window, min_periods=1)
                .over(over_cols)  # Apply per symbol
                * (1.0 / (window - 1.0))
            ).alias("close_vol"),
            (
                pl.col("log_oc_sq")
                .rolling_sum(window_size=window, min_periods=1)
                .over(over_cols)  # Apply per symbol
                * (1.0 / (window - 1.0))
            ).alias("open_vol"),
            (
                pl.col("rs")
                .rolling_sum(window_size=window, min_periods=1)
                .over(over_cols)  # Apply per symbol
                * (1.0 / (window - 1.0))
            ).alias("window_rs"),
        ]
    )
    return out


def yang_zhang(
    data: pl.DataFrame | pl.LazyFrame,
    window: str = "1m",
    trading_periods: int = 252,
    _column_name_high: str = "high",
    _column_name_low: str = "low",
    _column_name_open: str = "open",
    _column_name_close: str = "close",
    _avg_trading_days: bool = False,
    _drop_nulls: bool = True,
    _sort: bool = True,
) -> pl.LazyFrame:
    """
    Context: Toolbox || Category: Technical || Sub-Category: Volatility Helpers || **Command: _yang_zhang**.

    Yang-Zhang volatility is the combination of the overnight
    (close-to-open volatility), a weighted average of the Rogers-Satchell
    volatility and the day’s open-to-close volatility.
    """
    _check_required_columns(
        data,
        _column_name_high,
        _column_name_low,
        _column_name_open,
        _column_name_close,
    )
    sort_cols = _set_sort_cols(data, "symbol", "date")
    over_cols = _set_over_cols(data, "symbol")  # Get symbol for grouping

    if _sort and sort_cols:
        data = data.lazy().sort(sort_cols)
        for col in sort_cols:
            data = data.set_sorted(col)

    window_int: int = _window_format(
        window=window,
        _return_timedelta=True,
        _avg_trading_days=_avg_trading_days,
    ).days

    # Keep everything in lazy context and calculate per symbol
    data = (
        data.lazy()
        # Calculate log ratios per symbol
        .with_columns(
            [
                (pl.col(_column_name_high) / pl.col(_column_name_open))
                .log()
                .over(over_cols)
                .alias("log_ho"),
                (pl.col(_column_name_low) / pl.col(_column_name_open))
                .log()
                .over(over_cols)
                .alias("log_lo"),
                (pl.col(_column_name_close) / pl.col(_column_name_open))
                .log()
                .over(over_cols)
                .alias("log_co"),
                (pl.col(_column_name_open) / pl.col(_column_name_close).shift())
                .log()
                .over(over_cols)
                .alias("log_oc"),
                (
                    pl.col(_column_name_close)
                    / pl.col(_column_name_close).shift()
                )
                .log()
                .over(over_cols)
                .alias("log_cc"),
            ]
        )
        # Calculate squared terms and RS per symbol
        .with_columns(
            [
                (pl.col("log_oc").pow(2)).over(over_cols).alias("log_oc_sq"),
                (pl.col("log_cc").pow(2)).over(over_cols).alias("log_cc_sq"),
                (
                    pl.col("log_ho") * (pl.col("log_ho") - pl.col("log_co"))
                    + pl.col("log_lo") * (pl.col("log_lo") - pl.col("log_co"))
                )
                .over(over_cols)
                .alias("rs"),
            ]
        )
    )

    k = 0.34 / (1.34 + (window_int + 1) / (window_int - 1))
    # Pass over_cols to engine for per-symbol calculations
    data = _yang_zhang_engine(data=data, window=window_int, over_cols=over_cols)

    # Calculate final volatility per symbol
    result = (
        data.lazy()
        .with_columns(
            (
                (
                    pl.col("open_vol")
                    + k * pl.col("close_vol")
                    + (1 - k) * pl.col("window_rs")
                )
                .sqrt()
                .over(over_cols)  # Ensure final calculation is per symbol
                * np.sqrt(trading_periods)
                * 100
            ).alias(f"yz_volatility_pct_{window_int}D")
        )
        .select(
            pl.exclude(
                [
                    "log_ho",
                    "log_lo",
                    "log_co",
                    "log_oc",
                    "log_cc",
                    "log_oc_sq",
                    "log_cc_sq",
                    "rs",
                    "close_vol",
                    "open_vol",
                    "window_rs",
                ]
            )
        )
    )

    if _drop_nulls:
        return result.drop_nulls(subset=f"yz_volatility_pct_{window_int}D")
    return result


def squared_returns(
    data: pl.DataFrame | pl.LazyFrame,
    window: str = "1m",
    trading_periods: int = 252,
    _drop_nulls: bool = True,
    _avg_trading_days: bool = False,
    _column_name_returns: str = "log_returns",
    _sort: bool = True,
) -> pl.LazyFrame:
    """
    Calculate squared returns over a rolling window.

    Parameters
    ----------
    data : pl.DataFrame | pl.LazyFrame
        The input data containing the price information.
    window : str, optional
        The rolling window size for calculating squared returns, by default "1m".
    trading_periods : int, optional
        The number of trading periods in a year, used for scaling the result.
        The default is 252.
    _drop_nulls : bool, optional
        Whether to drop null values from the result, by default True.
    _column_name_returns : str, optional
        The name of the column containing the price data, by default "close".

    Returns
    -------
    pl.DataFrame | pl.LazyFrame
        The input data structure with an additional column for the rolling
        squared returns.
    """
    _check_required_columns(data, _column_name_returns)

    sort_cols = _set_sort_cols(data, "symbol", "date")
    over_cols = _set_over_cols(data, "symbol")  # Get symbol for grouping

    if _sort and sort_cols:
        data = data.lazy().sort(sort_cols)
        for col in sort_cols:
            data = data.set_sorted(col)

    window_int: int = _window_format(
        window=window,
        _return_timedelta=True,
        _avg_trading_days=_avg_trading_days,
    ).days

    # Keep everything in lazy context and calculate per symbol
    result = (
        data.lazy()
        # Calculate squared returns per symbol
        .with_columns(
            (
                (pl.col(_column_name_returns) * 100)
                .pow(2)
                .over(over_cols)  # Apply per symbol group
            ).alias("sq_log_returns_pct")
        )
        # Calculate rolling mean per symbol
        .with_columns(
            (
                pl.col("sq_log_returns_pct")
                .rolling_mean(window_size=window_int, min_periods=1)
                .over(over_cols)  # Apply per symbol group
            ).alias(f"sq_volatility_pct_{window_int}D")
        )
        .drop("sq_log_returns_pct")  # Remove intermediate calculation
    )

    if _drop_nulls:
        result = result.drop_nulls(subset=f"sq_volatility_pct_{window_int}D")
    return result
