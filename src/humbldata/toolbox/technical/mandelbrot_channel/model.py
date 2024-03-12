"""
Context: Toolbox || Category: Technical || **Command: calc_mandelbrot_channel**.

A command to generate a Mandelbrot Channel for any time series.
"""

from typing import Literal

import polars as pl

from humbldata.core.standard_models.abstract.errors import (
    HumblDataError,
)
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.standard_models.toolbox.technical.mandelbrotchannel import (
    MandelbrotChannelData,
    MandelbrotChannelQueryParams,
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
    rv_adjustment: bool = True,
    _rv_method: str = "std",
    _rs_method: Literal["RS", "RS_mean", "RS_max", "RS_min"] = "RS",
    *,
    _rv_grouped_mean: bool = True,
    _live_price: bool = True,
) -> pl.DataFrame | pl.LazyFrame:
    """
    Context: Toolbox || Category: Technical || Sub-Category: Mandelbrot Channel || **Command: calc_mandelbrot_channel`.

    Calculates the Mandelbrot Channel for a given time series based on the
    provided standard and extra parameters.

    Parameters
    ----------
    data: pl.DataFrame | pl.LazyFrame
        The time series data for which to calculate the Mandelbrot Channel.
    window: str, default "1m"
        The window size for the calculation, specified as a string.
    rv_adjustment: bool, default True
        Whether to adjust the calculation for realized volatility.
    _rv_grouped_mean: bool, default True
        Whether to use the grouped mean in the realized volatility calculation.
    _rv_method: str, default "std"
        The method to use for calculating realized volatility. You only need to
        supply a value if `rv_adjustment` is True.
    _rs_method: str, default "RS"
        The method to use for calculating the range over standard deviation.
        You can choose either RS/RS_mean/RS_min/RS_max. This changes the width of
        the calculated Mandelbrot Channel
    _live_price: bool, default True
        Whether to use live price data in the calculation. This may add a
        significant amount of time to the calculation (1-3s)

    Returns
    -------
    pl.DataFrame | pl.LazyFrame
        The calculated Mandelbrot Channel data for the given time series.
    """
    # Setup ====================================================
    window_int = _window_format(window, _return_timedelta=True)
    sort_cols = _set_sort_cols(data, "symbol", "date")

    data = data.lazy()
    # Step 1: Collect Price Data -------------------------------------------
    # Step X: Add window bins ----------------------------------------------
    # We want date grouping, non-overlapping window bins
    data1 = add_window_index(data, window=window)

    # Step X: Calculate Log Returns + Rvol ---------------------------------
    if "log_returns" not in data1.columns:
        data2 = log_returns(data1, _column_name="close")
    else:
        data2 = data1

    # Step X: Calculate Log Mean Series ------------------------------------
    if isinstance(data2, pl.DataFrame | pl.LazyFrame):
        data3 = mean(data2)
    else:
        msg = "A series was passed to `mean()` calculation. Please provide a DataFrame or LazyFrame."
        raise HumblDataError(msg)
    # Step X: Calculate Mean De-trended Series -----------------------------
    data4 = detrend(
        data3, _detrend_value_col="window_mean", _detrend_col="log_returns"
    )
    # Step X: Calculate Cumulative Deviate Series --------------------------
    data5 = cum_sum(data4, _column_name="detrended_log_returns")
    # Step X: Calculate Mandelbrot Range -----------------------------------
    data6 = range_(data5, _column_name="cum_sum")
    # Step X: Calculate Standard Deviation ---------------------------------
    data7 = std(data6, _column_name="cum_sum")
    # Step X: Calculate Range (R) & Standard Deviation (S) -----------------
    if rv_adjustment:
        # Step 8.1: Calculate Realized Volatility --------------------------
        data7 = calc_realized_volatility(
            data=data7,
            window=window,
            method=_rv_method,
            grouped_mean=_rv_grouped_mean,
        )
        # rename col for easy selection
        for col in data7.columns:
            if "volatility_pct" in col:
                data7 = data7.rename({col: "realized_volatility"})
        # Step 8.2: Calculate Volatility Bucket Stats ----------------------
        data7 = vol_buckets(data=data7, lo_quantile=0.3, hi_quantile=0.65)
        data7 = vol_filter(data7)

    # Step X: Calculate RS -------------------------------------------------
    data8 = data7.sort(sort_cols).with_columns(
        (pl.col("cum_sum_range") / pl.col("cum_sum_std")).alias("RS")
    )

    # Step X: Collect Recent Prices ----------------------------------------
    if _live_price:
        symbols = (
            data.select("symbol").unique().sort("symbol").collect().to_series()
        )
        recent_prices = get_latest_price(symbols)
    else:
        recent_prices = None

    # Step X: Calculate Rescaled Price Range ------------------------------
    out = price_range(
        data=data8,
        recent_price_data=recent_prices,
        rs_method=_rs_method,
        _rv_adjustment=rv_adjustment,
    )

    return out


async def acalc_mandelbrot_channel(
    data,
    window="1m",
    rv_adjustment=True,
    _rv_method="std",
    _rs_method="RS",
    _rv_grouped_mean=True,
    _live_price=True,
):
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
        _rv_method=_rv_method,
        _rs_method=_rs_method,
        _rv_grouped_mean=_rv_grouped_mean,
        _live_price=_live_price,
    )
