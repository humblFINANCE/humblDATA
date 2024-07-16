"""
Context: Toolbox || Category: Technical || **Command: calc_mandelbrot_channel**.

A command to generate a Mandelbrot Channel for any time series.
"""

import asyncio
from typing import Literal

import nest_asyncio
import polars as pl
from polars import lazyframe

from humbldata.core.standard_models.abstract.errors import (
    HumblDataError,
)
from humbldata.core.utils.openbb_helpers import get_latest_price
from humbldata.toolbox.technical.mandelbrot_channel.helpers import (
    add_window_index,
    price_range,
    vol_buckets,
    vol_filter,
)
from humbldata.toolbox.technical.volatility.realized_volatility_model import (
    calc_realized_volatility,
)
from humbldata.toolbox.toolbox_helpers import (
    _set_sort_cols,
    _window_format,
    cum_sum,
    detrend,
    log_returns,
    mean,
    range_,
    std,
)


def calc_mandelbrot_channel(
    data: pl.DataFrame | pl.LazyFrame,
    window: str = "1m",
    rv_method: str = "std",
    rs_method: Literal["RS", "RS_mean", "RS_max", "RS_min"] = "RS",
    *,
    rv_adjustment: bool = True,
    rv_grouped_mean: bool = True,
    live_price: bool = True,
    **kwargs,
) -> pl.LazyFrame:
    """
    Context: Toolbox || Category: Technical || **Command: calc_mandelbrot_channel**.

    This command calculates the Mandelbrot Channel for a given time series, utilizing various parameters to adjust the calculation. The Mandelbrot Channel provides insights into the volatility and price range of a stock over a specified window.

    Parameters
    ----------
    data: pl.DataFrame | pl.LazyFrame
        The time series data for which to calculate the Mandelbrot Channel.
        There needs to be a `close` and `date` column.
    window: str, default "1m"
        The window size for the calculation, specified as a string. This
        determines the period over which the channel is calculated.
    rv_adjustment: bool, default True
        Adjusts the calculation for realized volatility. If True, filters the
        data to include only observations within the current volatility bucket
        of the stock.
    rv_grouped_mean: bool, default True
        Determines whether to use the grouped mean in the realized volatility
        calculation.
    rv_method: str, default "std"
        Specifies the method for calculating realized volatility, applicable
        only if `rv_adjustment` is True.
    rs_method: str, default "RS"
        Defines the method for calculating the range over standard deviation,
        affecting the width of the Mandelbrot Channel. Options include RS,
        RS_mean, RS_min, and RS_max.
    live_price: bool, default True
        Indicates whether to incorporate live price data into the calculation,
        which may extend the calculation time by 1-3 seconds.
    **kwargs
        Additional keyword arguments to pass to the function, if you want to
        change the behavior or pass parameters to internal functions.

    Returns
    -------
    pl.LazyFrame
        A LazyFrame containing the calculated Mandelbrot Channel data for the specified time series.

    Notes
    -----
    The function returns a pl.LazyFrame; remember to call `.collect()` on the result to obtain a DataFrame. This lazy evaluation strategy postpones the calculation until it is explicitly requested.

    Example
    -------
    To calculate the Mandelbrot Channel for a yearly window with adjustments for realized volatility using the 'yz' method, and incorporating live price data:

    ```python
    mandelbrot_channel = calc_mandelbrot_channel(
        data,
        window="1y",
        rv_adjustment=True,
        rv_method="yz",
        rv_grouped_mean=False,
        rs_method="RS",
        live_price=True
    ).collect()
    ```
    """
    # Setup ====================================================================
    window_datetime = _window_format(window, _return_timedelta=True)
    sort_cols = _set_sort_cols(data, "symbol", "date")

    data = data.lazy()
    # Step 1: Collect Price Data -----------------------------------------------
    # Step X: Add window bins --------------------------------------------------
    # We want date grouping, non-overlapping window bins
    data1 = add_window_index(data, window=window)

    # Step X: Calculate Log Returns + Rvol -------------------------------------
    if "log_returns" not in data1.collect_schema().names():
        data2 = log_returns(data1, _column_name="close")
    else:
        data2 = data1

    # Step X: Calculate Log Mean Series ----------------------------------------
    if isinstance(data2, pl.DataFrame | pl.LazyFrame):
        data3 = mean(data2)
    else:
        msg = "A series was passed to `mean()` calculation. Please provide a DataFrame or LazyFrame."
        raise HumblDataError(msg)
    # Step X: Calculate Mean De-trended Series ---------------------------------
    data4 = detrend(
        data3, _detrend_value_col="window_mean", _detrend_col="log_returns"
    )
    # Step X: Calculate Cumulative Deviate Series ------------------------------
    data5 = cum_sum(data4, _column_name="detrended_log_returns")
    # Step X: Calculate Mandelbrot Range ---------------------------------------
    data6 = range_(data5, _column_name="cum_sum")
    # Step X: Calculate Standard Deviation -------------------------------------
    data7 = std(data6, _column_name="cum_sum")
    # Step X: Calculate Range (R) & Standard Deviation (S) ---------------------
    if rv_adjustment:
        # Step 8.1: Calculate Realized Volatility ------------------------------
        data7 = calc_realized_volatility(
            data=data7,
            window=window,
            method=rv_method,
            grouped_mean=rv_grouped_mean,
        )
        # rename col for easy selection
        for col in data7.collect_schema().names():
            if "volatility_pct" in col:
                data7 = data7.rename({col: "realized_volatility"})
        # Step 8.2: Calculate Volatility Bucket Stats --------------------------
        data7 = vol_buckets(data=data7, lo_quantile=0.3, hi_quantile=0.65)
        data7 = vol_filter(
            data7
        )  # removes rows that arent in the same vol bucket

    # Step X: Calculate RS -----------------------------------------------------
    data8 = data7.sort(sort_cols).with_columns(
        (pl.col("cum_sum_range") / pl.col("cum_sum_std")).alias("RS")
    )

    # Step X: Collect Recent Prices --------------------------------------------
    if live_price:
        symbols = (
            data.select("symbol").unique().sort("symbol").collect().to_series()
        )
        recent_prices = get_latest_price(symbols)
    else:
        recent_prices = None

    # Step X: Calculate Rescaled Price Range ----------------------------------
    out = price_range(
        data=data8,
        recent_price_data=recent_prices,
        rs_method=rs_method,
        _rv_adjustment=rv_adjustment,
    )

    return out


async def acalc_mandelbrot_channel(
    data: pl.DataFrame | pl.LazyFrame,
    window: str = "1m",
    rv_adjustment: bool = True,
    rv_method: str = "std",
    rs_method: Literal["RS", "RS_mean", "RS_max", "RS_min"] = "RS",
    *,
    rv_grouped_mean: bool = True,
    live_price: bool = True,
    **kwargs,
) -> pl.DataFrame | pl.LazyFrame:
    """
    Context: Toolbox || Category: Technical || Sub-Category: Mandelbrot Channel || **Command: acalc_mandelbrot_channel**.

    Asynchronous wrapper for calc_mandelbrot_channel.
    This function allows calc_mandelbrot_channel to be called in an async context.

    Notes
    -----
    This does not make `calc_mandelbrot_channel()` non-blocking or asynchronous.
    """
    # Directly call the synchronous calc_mandelbrot_channel function
    return calc_mandelbrot_channel(
        data=data,
        window=window,
        rv_adjustment=rv_adjustment,
        rv_method=rv_method,
        rs_method=rs_method,
        rv_grouped_mean=rv_grouped_mean,
        live_price=live_price,
        **kwargs,
    )


async def _acalc_mandelbrot_channel_historical_engine(
    data: pl.DataFrame | pl.LazyFrame,
    window: str = "1m",
    rv_adjustment: bool = True,
    rv_method: str = "std",
    rs_method: Literal["RS", "RS_mean", "RS_max", "RS_min"] = "RS",
    *,
    rv_grouped_mean: bool = True,
    live_price: bool = True,
    **kwargs,
) -> pl.LazyFrame:
    """
    Context: Toolbox || Category: Technical || Sub-Category: Mandelbrot Channel || **Command: _calc_mandelbrot_channel_historical_engine**.

    This function acts as the internal logic to the wrapper function
    `calc_mandelbrot_channel_historical()`.
    """
    window_days = _window_format(window, _return_timedelta=True)
    start_date = data.lazy().select(pl.col("date")).min().collect().row(0)[0]
    start_date = start_date + window_days
    end_date = data.lazy().select("date").max().collect().row(0)[0]

    if start_date >= end_date:
        msg = f"You set <historical=True> \n\
        This calculation needs *at least* one window of data. \n\
        The (start date + window) is: {start_date} and the dataset ended: {end_date}. \n\
        Please adjust dates accordingly."
        raise HumblDataError(msg)

    dates = (
        data.lazy()
        .select(pl.col("date"))
        .filter(pl.col("date") >= start_date)
        .unique()
        .sort("date")
        .collect()
        .to_series()
    )

    tasks = [
        asyncio.create_task(
            acalc_mandelbrot_channel(
                data=data.filter(pl.col("date") <= date),
                window=window,
                rv_adjustment=rv_adjustment,
                rv_method=rv_method,
                rs_method=rs_method,
                rv_grouped_mean=rv_grouped_mean,
                live_price=live_price,
                **kwargs,
            )
        )
        for date in dates
    ]

    lazyframes = await asyncio.gather(*tasks)
    out = (
        await pl.concat(lazyframes, how="vertical")
        .sort(["symbol", "date"])
        .rename({"recent_price": "close_price"})
        .collect_async()
    )

    # out = await pl.collect_all_async(lazyframes)

    return out.lazy()


def calc_mandelbrot_channel_historical(
    data: pl.DataFrame | pl.LazyFrame,
    window: str = "1m",
    rv_adjustment: bool = True,
    rv_method: str = "std",
    rs_method: Literal["RS", "RS_mean", "RS_max", "RS_min"] = "RS",
    *,
    rv_grouped_mean: bool = True,
    live_price: bool = True,
    **kwargs,
) -> pl.LazyFrame:
    """
    Context: Toolbox || Category: Technical || Sub-Category: Mandelbrot Channel || **Command: calc_mandelbrot_channel_historical**.

    Calculates the Mandelbrot Channel for a given time series based on the
    provided standard and extra parameters, over time! This means that instead
    of using the dataset to calculate one statistic at the current point in time,
    this function starts at the beginning of the dataset and calculates the statistic
    for date present in the dataset, up to the current point in time.
    """
    nest_asyncio.apply()

    return asyncio.run(
        _acalc_mandelbrot_channel_historical_engine(
            data=data,
            window=window,
            rv_adjustment=rv_adjustment,
            rv_method=rv_method,
            rs_method=rs_method,
            rv_grouped_mean=rv_grouped_mean,
            live_price=live_price,
            **kwargs,
        )
    )
