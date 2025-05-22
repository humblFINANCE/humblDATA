"""
Context: Toolbox || Category: Technical || **Command: calc_humbl_channel**.

A command to generate a Mandelbrot Channel for any time series.
"""

import asyncio
import concurrent.futures
import multiprocessing
from functools import partial
from typing import Literal

import polars as pl
import uvloop

from humbldata.core.standard_models.abstract.errors import (
    HumblDataError,
)
from humbldata.core.standard_models.abstract.warnings import collect_warnings
from humbldata.core.utils.core_helpers import run_async
from humbldata.toolbox.technical.humbl_channel.helpers import (
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

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


@collect_warnings
def calc_humbl_channel(  # noqa: PLR0913
    data: pl.DataFrame | pl.LazyFrame,
    window: str = "1m",
    rv_method: Literal[
        "std",
        "parkinson",
        "garman_klass",
        "gk",
        "hodges_tompkins",
        "ht",
        "rogers_satchell",
        "rs",
        "yang_zhang",
        "yz",
        "squared_returns",
        "sq",
    ] = "std",
    rs_method: Literal["RS", "RS_mean", "RS_max", "RS_min"] = "RS",
    *,
    rv_adjustment: bool = True,
    rv_grouped_mean: bool = False,
    yesterday_close: bool = False,
    **kwargs,
) -> pl.LazyFrame:
    """
    Context: Toolbox || Category: Technical || **Command: calc_humbl_channel**.

    This command calculates the Channel for a given time series, utilizing various parameters to adjust the calculation. The Mandelbrot Channel provides insights into the volatility and price range of a stock over a specified window.

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
    rv_grouped_mean: bool, default False
        Determines whether to use the grouped mean in the realized volatility
        calculation. If False, no grouped mean is used.
    rv_method: str, default "std"
        Specifies the method for calculating realized volatility, applicable
        only if `rv_adjustment` is True.
    rs_method: str, default "RS"
        Defines the method for calculating the range over standard deviation,
        affecting the width of the Mandelbrot Channel. Options include RS,
        RS_mean, RS_min, and RS_max.
    yesterday_close: bool, default False
        If True, use yesterday's close price (second to last row). If False, use today's close price (last row).
    **kwargs
        Additional keyword arguments to pass to the function, if you want to
        change the behavior or pass parameters to internal functions.

    Returns
    -------
    pl.LazyFrame
        A LazyFrame containing the calculated Mandelbrot Channel data for the specified time series.

    Notes
    -----
    The function returns a pl.LazyFrame; remember to call `.collect()` on the
    result to obtain a DataFrame. This lazy evaluation strategy postpones the
    calculation until it is explicitly requested.

    For the humbl_channel calculation, we want to loop over each symbol and the
    window_index

    Example
    -------
    To calculate the Mandelbrot Channel for a yearly window with adjustments for realized volatility using the 'yz' method:

    ```python
    humbl_channel = calc_humbl_channel(
        data,
        window="1y",
        rv_adjustment=True,
        rv_method="yz",
        rv_grouped_mean=False,
        rs_method="RS",
        yesterday_close=False
    ).collect()
    ```
    """
    # Setup ====================================================================
    sort_cols = _set_sort_cols(data, "symbol", "date")

    data = data.lazy()

    # Step 1: Add window bins for non-overlapping date grouping
    data1 = add_window_index(data, window=window)

    # Step 2: Calculate log returns if not already present
    if "log_returns" not in data1.collect_schema().names():
        data2 = log_returns(data1, _column_name="close")
    else:
        data2 = data1

    # Step 3: Calculate Log Mean series for the window bins
    if isinstance(data2, pl.DataFrame | pl.LazyFrame):
        data3 = mean(data2)
    else:
        msg = "A series was passed to `mean()` calculation. Please provide a DataFrame or LazyFrame."
        raise HumblDataError(msg)
    # Step 4: Calculate Mean De-trended Series ---------------------------------
    data4 = detrend(
        data3, _detrend_value_col="window_mean", _detrend_col="log_returns"
    )
    # Step 5: Calculate Cumulative Deviate Series ------------------------------
    data5 = cum_sum(data4, _column_name="detrended_log_returns")

    # Step 6: Calculate range of cumulative sums within bins
    data6 = range_(data5, _column_name="cum_sum")

    # Step 7: Calculate standard deviation of cumulative sums
    data7 = std(data6, _column_name="cum_sum")

    # If momentum is not NOne, then add the momentum calc step here.

    # Step 8: Apply realized volatility adjustments if requested
    if rv_adjustment:
        # Calculate realized volatility using specified method
        data7 = calc_realized_volatility(
            data=data7,
            window=window,
            method=rv_method,
            grouped_mean=None if not rv_grouped_mean else [1, 5, 10],
        )
        # rename col for easy selection
        for col in data7.collect_schema().names():
            if "volatility_pct" in col:
                data7 = data7.rename({col: "realized_volatility"})

        # Filter data based on volatility buckets
        data7 = vol_buckets(data=data7, lo_quantile=0.3, hi_quantile=0.65)
        data7 = vol_filter(data7)

    # Step 9: Calculate Rescaled Range (RS) statistic
    data8 = data7.sort(sort_cols).with_columns(
        [(pl.col("cum_sum_range") / pl.col("cum_sum_std")).alias("RS")]
    )

    # Step 10: Calculate Rescaled Price Range ----------------------------------
    out = price_range(
        data=data8,
        rs_method=rs_method,
        _rv_adjustment=rv_adjustment,
        yesterday_close=yesterday_close,
    )

    return out


def _calc_humbl_for_date(
    date,
    data,
    window,
    rv_adjustment,
    rv_method,
    rs_method,
    rv_grouped_mean,
    yesterday_close,
    use_live_price=None,
    **kwargs,
):
    """Calculate Mandelbrot Channel for a single date."""
    # Only include data up to the target date, this prevents look-ahead bias
    filtered_data = data.filter(pl.col("date") <= date)

    return calc_humbl_channel(
        data=filtered_data,
        window=window,
        rv_adjustment=rv_adjustment,
        rv_method=rv_method,
        rs_method=rs_method,
        rv_grouped_mean=rv_grouped_mean,
        yesterday_close=yesterday_close,
        **kwargs,
    )


def calc_humbl_channel_historical_concurrent(
    data: pl.DataFrame | pl.LazyFrame,
    window: str = "1m",
    rv_method: str = "std",
    rs_method: Literal["RS", "RS_mean", "RS_max", "RS_min"] = "RS",
    *,
    rv_adjustment: bool = True,
    rv_grouped_mean: bool = True,
    yesterday_close: bool = True,
    max_workers: int | None = None,
    use_processes: bool = False,
    **kwargs,
) -> pl.LazyFrame:
    """
    Calculate the Humbl Channel historically using concurrent.futures.

    Parameters:
    -----------
    max_workers : int, optional
        Maximum number of workers to use. If None, it uses the default for ProcessPoolExecutor
        or ThreadPoolExecutor (usually the number of processors on the machine, multiplied by 5).
    use_processes : bool, default True
        If True, use ProcessPoolExecutor, otherwise use ThreadPoolExecutor.

    Other parameters are the same as calc_humbl_channel_historical.
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

    # Prepare the partial function with all arguments except the date
    calc_func = partial(
        _calc_humbl_for_date,
        data=data,
        window=window,
        rv_adjustment=rv_adjustment,
        rv_method=rv_method,
        rs_method=rs_method,
        rv_grouped_mean=rv_grouped_mean,
        yesterday_close=yesterday_close,
        **kwargs,
    )

    # Choose the appropriate executor
    executor_class = (
        concurrent.futures.ProcessPoolExecutor
        if use_processes
        else concurrent.futures.ThreadPoolExecutor
    )
    # Use concurrent.futures to calculate in parallel
    with executor_class(max_workers=max_workers) as executor:
        futures = [executor.submit(calc_func, date) for date in dates]
        results = [
            future.result()
            for future in concurrent.futures.as_completed(futures)
        ]

    # Combine results
    out = pl.concat(results, how="vertical").sort(["symbol", "date"])

    return out.lazy()


async def acalc_humbl_channel(  # noqa: PLR0913
    data: pl.DataFrame | pl.LazyFrame,
    window: str = "1m",
    rv_method: str = "std",
    rs_method: Literal["RS", "RS_mean", "RS_max", "RS_min"] = "RS",
    *,
    rv_adjustment: bool = True,
    rv_grouped_mean: bool = True,
    yesterday_close: bool = True,
    **kwargs,
) -> pl.DataFrame | pl.LazyFrame:
    """
    Context: Toolbox || Category: Technical || Sub-Category: Humbl Channel || **Command: acalc_humbl_channel**.

    Asynchronous wrapper for calc_humbl_channel.
    This function allows calc_humbl_channel to be called in an async context.

    Notes
    -----
    This does not make `calc_humbl_channel()` non-blocking or asynchronous.
    """
    # Directly call the synchronous calc_humbl_channel function

    return calc_humbl_channel(
        data=data,
        window=window,
        rv_adjustment=rv_adjustment,
        rv_method=rv_method,
        rs_method=rs_method,
        rv_grouped_mean=rv_grouped_mean,
        yesterday_close=yesterday_close,
        **kwargs,
    )


async def _acalc_humbl_channel_historical_engine(  # noqa: PLR0913
    data: pl.DataFrame | pl.LazyFrame,
    window: str = "1m",
    rv_method: str = "std",
    rs_method: Literal["RS", "RS_mean", "RS_max", "RS_min"] = "RS",
    *,
    rv_adjustment: bool = True,
    rv_grouped_mean: bool = True,
    yesterday_close: bool = True,
    **kwargs,
) -> pl.LazyFrame:
    """
    Context: Toolbox || Category: Technical || Sub-Category: Humbl Channel || **Command: _calc_humbl_channel_historical_engine**.

    This function acts as the internal logic to the wrapper function
    `calc_humbl_channel_historical()`.
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
            acalc_humbl_channel(
                data=data.filter(pl.col("date") <= date),
                window=window,
                rv_adjustment=rv_adjustment,
                rv_method=rv_method,
                rs_method=rs_method,
                rv_grouped_mean=rv_grouped_mean,
                yesterday_close=yesterday_close,
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


def calc_humbl_channel_historical(  # noqa: PLR0913
    data: pl.DataFrame | pl.LazyFrame,
    window: str = "1m",
    rv_method: str = "std",
    rs_method: Literal["RS", "RS_mean", "RS_max", "RS_min"] = "RS",
    *,
    rv_adjustment: bool = True,
    rv_grouped_mean: bool = True,
    yesterday_close: bool = True,
    **kwargs,
) -> pl.LazyFrame:
    """
    Context: Toolbox || Category: Technical || Sub-Category: Humbl Channel || **Command: calc_humbl_channel_historical**.

    This function calculates the Humbl Channel for historical data.

    Synchronous wrapper for the asynchronous Humbl Channel historical calculation.

    Parameters
    ----------
    The parameters for this function are the same as those for calc_humbl_channel().
    Please refer to the documentation of calc_humbl_channel() for a detailed
    description of each parameter.

    Returns
    -------
    pl.LazyFrame
        A LazyFrame containing the historical Mandelbrot Channel calculations.
    """
    return run_async(
        _acalc_humbl_channel_historical_engine(
            data=data,
            window=window,
            rv_adjustment=rv_adjustment,
            rv_method=rv_method,
            rs_method=rs_method,
            rv_grouped_mean=rv_grouped_mean,
            yesterday_close=yesterday_close,
            **kwargs,
        )
    )


def calc_humbl_channel_historical_mp(
    data: pl.DataFrame | pl.LazyFrame,
    window: str = "1m",
    rv_adjustment: bool = True,
    rv_method: str = "std",
    rs_method: Literal["RS", "RS_mean", "RS_max", "RS_min"] = "RS",
    *,
    rv_grouped_mean: bool = True,
    yesterday_close: bool = True,
    n_processes: int = 1,
    **kwargs,
) -> pl.LazyFrame:
    """
    Calculate the Humbl Channel historically using multiprocessing.

    Parameters:
    -----------
    n_processes : int, optional
        Number of processes to use. If None, it uses all available cores.

    Other parameters are the same as calc_humbl_channel_historical.
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

    # Prepare the partial function with all arguments except the date
    calc_func = partial(
        _calc_humbl_for_date,
        data=data,
        window=window,
        rv_adjustment=rv_adjustment,
        rv_method=rv_method,
        rs_method=rs_method,
        rv_grouped_mean=rv_grouped_mean,
        yesterday_close=yesterday_close,
        **kwargs,
    )

    # Use multiprocessing to calculate in parallel
    with multiprocessing.Pool(processes=n_processes) as pool:
        results = pool.map(calc_func, dates)

    # Combine results
    out = pl.concat(results, how="vertical").sort(["symbol", "date"])

    return out.lazy()
