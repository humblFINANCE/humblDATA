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
    window_int: int = _window_format(
        window, _return_timedelta=True, _avg_trading_days=_avg_trading_days
    ).days
    if isinstance(data, pl.Series):
        return data.rolling_std(window_size=window_int, min_periods=1)
    else:
        sort_cols = _set_sort_cols(data, "symbol", "date")
        if _sort:
            data = data.lazy().sort(sort_cols)
        # convert window_timedelta to days to use fixed window
        result = (
            data.lazy()
            .set_sorted(sort_cols)
            .with_columns(
                (
                    pl.col(_column_name_returns).rolling_std(
                        window_size=window_int,
                        min_periods=2,  # using min_periods=2, bc if min_periods=1, the first value will be 0.
                        by="date",
                    )
                    * math.sqrt(trading_periods)
                    * 100
                ).alias(f"std_volatility_pct_{window_int}D")
            )
        )
    if _drop_nulls:
        return result.drop_nulls(subset=f"std_volatility_pct_{window_int}D")
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
    if _sort:
        data = data.lazy().sort(sort_cols)

    var1 = 1.0 / (4.0 * math.log(2.0))
    var2 = (
        data.lazy()
        .set_sorted(sort_cols)
        .select((pl.col(_column_name_high) / pl.col(_column_name_low)).log())
        .collect()
        .to_series()
    )
    rs = var1 * var2**2

    window_int: int = _window_format(
        window, _return_timedelta=True, _avg_trading_days=_avg_trading_days
    ).days
    result = (
        data.lazy()
        .set_sorted(sort_cols)
        .with_columns(
            (
                rs.rolling_map(
                    _annual_vol, window_size=window_int, min_periods=1
                )
                * 100
            ).alias(f"parkinson_volatility_pct_{window_int}D")
        )
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
    _column_name_close: str = "adj_close",
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
        default "adj_close".
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
    if _sort:
        data = data.lazy().sort(sort_cols)
    log_hi_lo = (
        data.lazy()
        .set_sorted(sort_cols)
        .select((pl.col(_column_name_high) / pl.col(_column_name_low)).log())
        .collect()
        .to_series()
    )
    log_close_open = (
        data.lazy()
        .select((pl.col(_column_name_close) / pl.col(_column_name_open)).log())
        .collect()
        .to_series()
    )
    rs: pl.Series = 0.5 * log_hi_lo**2 - (2 * np.log(2) - 1) * log_close_open**2

    window_int: int = _window_format(
        window, _return_timedelta=True, _avg_trading_days=_avg_trading_days
    ).days
    result = data.lazy().with_columns(
        (
            rs.rolling_map(_annual_vol, window_size=window_int, min_periods=1)
            * 100
        ).alias(f"gk_volatility_pct_{window_int}D")
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
    # When calculating rv_mean, need a different adjustment factor,
    # so window doesn't influence the Volatility_mean
    # RV_MEAN

    # Define Window Size
    window_timedelta = _window_format(
        window, _return_timedelta=True, _avg_trading_days=_avg_trading_days
    )
    # Calculate STD, assigned to `vol`
    if isinstance(data, pl.Series):
        vol = data.rolling_std(window_size=window_timedelta.days, min_periods=1)
    else:
        sort_cols = _set_sort_cols(data, "symbol", "date")
        if _sort:
            data = data.lazy().sort(sort_cols)
        vol = (
            data.lazy()
            .set_sorted(sort_cols)
            .select(
                pl.col(_column_name_returns).rolling_std(
                    window_size=window_timedelta, min_periods=1, by="date"
                )
                * np.sqrt(trading_periods)
            )
        )

    # Assign window size to h for adjustment
    h: int = window_timedelta.days

    if isinstance(data, pl.Series):
        count = data.len()
    elif isinstance(data, pl.LazyFrame):
        count = data.collect().shape[0]
    else:
        count = data.shape[0]

    n = (count - h) + 1
    adj_factor = 1.0 / (1.0 - (h / n) + ((h**2 - 1) / (3 * n**2)))

    if isinstance(data, pl.Series):
        return (vol * adj_factor) * 100
    else:
        result = data.lazy().with_columns(
            ((vol.collect() * adj_factor) * 100)
            .to_series()
            .alias(f"ht_volatility_pct_{h}D")
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
    _column_name_close: str = "adj_close",
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
    _column_name_close : str, default "adj_close"
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
    if _sort:
        data = data.lazy().sort(sort_cols)
    # assign window
    window_int: int = _window_format(
        window=window,
        _return_timedelta=True,
        _avg_trading_days=_avg_trading_days,
    ).days

    data = (
        data.lazy()
        .set_sorted(sort_cols)
        .with_columns(
            [
                (pl.col(_column_name_high) / pl.col(_column_name_open))
                .log()
                .alias("log_ho"),
                (pl.col(_column_name_low) / pl.col(_column_name_open))
                .log()
                .alias("log_lo"),
                (pl.col(_column_name_close) / pl.col(_column_name_open))
                .log()
                .alias("log_co"),
            ]
        )
        .with_columns(
            (
                pl.col("log_ho") * (pl.col("log_ho") - pl.col("log_co"))
                + pl.col("log_lo") * (pl.col("log_lo") - pl.col("log_co"))
            ).alias("rs")
        )
    )
    result = data.lazy().with_columns(
        (
            pl.col("rs").rolling_map(
                _annual_vol, window_size=window_int, min_periods=1
            )
            * 100
        ).alias(f"rs_volatility_pct_{window_int}D")
    )
    if _drop_nulls:
        result = result.drop_nulls(subset=f"rs_volatility_pct_{window_int}D")
    return result


def _yang_zhang_engine(
    data: pl.DataFrame | pl.LazyFrame,
    window: int,
) -> pl.DataFrame | pl.LazyFrame:
    _check_required_columns(data, "log_cc_sq", "log_oc_sq", "rs")

    out = data.lazy().with_columns(
        [
            (
                pl.col("log_cc_sq").rolling_sum(
                    window_size=window, min_periods=1
                )
                * (1.0 / (window - 1.0))
            ).alias("close_vol"),
            (
                pl.col("log_oc_sq").rolling_sum(
                    window_size=window, min_periods=1
                )
                * (1.0 / (window - 1.0))
            ).alias("open_vol"),
            (
                pl.col("rs").rolling_sum(window_size=window, min_periods=1)
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
    _column_name_close: str = "adj_close",
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
    # check required columns
    _check_required_columns(
        data,
        _column_name_high,
        _column_name_low,
        _column_name_open,
        _column_name_close,
    )
    sort_cols = _set_sort_cols(data, "symbol", "date")
    if _sort:
        data = data.lazy().sort(sort_cols)

    # assign window
    window_int: int = _window_format(
        window=window,
        _return_timedelta=True,
        _avg_trading_days=_avg_trading_days,
    ).days

    data = (
        data.lazy()
        .set_sorted(sort_cols)
        .with_columns(
            [
                (pl.col(_column_name_high) / pl.col(_column_name_open))
                .log()
                .alias("log_ho"),
                (pl.col(_column_name_low) / pl.col(_column_name_open))
                .log()
                .alias("log_lo"),
                (pl.col(_column_name_close) / pl.col(_column_name_open))
                .log()
                .alias("log_co"),
                (pl.col(_column_name_open) / pl.col(_column_name_close).shift())
                .log()
                .alias("log_oc"),
                (
                    pl.col(_column_name_close)
                    / pl.col(_column_name_close).shift()
                )
                .log()
                .alias("log_cc"),
            ]
        )
        .with_columns(
            [
                (pl.col("log_oc") ** 2).alias("log_oc_sq"),
                (pl.col("log_cc") ** 2).alias("log_cc_sq"),
                (
                    pl.col("log_ho") * (pl.col("log_ho") - pl.col("log_co"))
                    + pl.col("log_lo") * (pl.col("log_lo") - pl.col("log_co"))
                ).alias("rs"),
            ]
        )
    )

    k = 0.34 / (1.34 + (window_int + 1) / (window_int - 1))
    data = _yang_zhang_engine(data=data, window=window_int)
    result = (
        data.lazy()
        .with_columns(
            (
                (
                    pl.col("open_vol")
                    + k * pl.col("close_vol")
                    + (1 - k) * pl.col("window_rs")
                ).sqrt()
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
        The name of the column containing the price data, by default "adj_close".

    Returns
    -------
    pl.DataFrame | pl.LazyFrame
        The input data structure with an additional column for the rolling
        squared returns.
    """
    _check_required_columns(data, _column_name_returns)

    sort_cols = _set_sort_cols(data, "symbol", "date")
    if _sort:
        data = data.lazy().sort(sort_cols)

    # assign window
    window_int: int = _window_format(
        window=window,
        _return_timedelta=True,
        _avg_trading_days=_avg_trading_days,
    ).days

    data = (
        data.lazy()
        .set_sorted(sort_cols)
        .with_columns(
            ((pl.col(_column_name_returns) * 100) ** 2).alias(
                "sq_log_returns_pct"
            )
        )
    )
    # Calculate rolling squared returns
    result = (
        data.lazy()
        .with_columns(
            pl.col("sq_log_returns_pct")
            .rolling_mean(window_size=window_int, min_periods=1)
            .alias(f"sq_volatility_pct_{window_int}D")
        )
        .drop("sq_log_returns_pct")
    )
    if _drop_nulls:
        result = result.drop_nulls(subset=f"sq_volatility_pct_{window_int}D")
    return result
