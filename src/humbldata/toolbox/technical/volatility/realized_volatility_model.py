"""
Context: Toolbox || Category: Technical || **Command: calc_realized_volatility**.

A command to generate Realized Volatility for any time series.
"""

import inspect
from typing import Literal

import polars as pl

from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.standard_models.toolbox.technical.realized_volatility import (
    RealizedVolatilityData,
    RealizedVolatilityQueryParams,
)
from humbldata.toolbox.technical.volatility.realized_volatility_helpers import (
    garman_klass,
    hodges_tompkins,
    parkinson,
    rogers_satchell,
    squared_returns,
    std,
    yang_zhang,
)

# Mapping of method names to functions, consider switching to ENUM class for scalability and robustness and safety
VOLATILITY_METHODS = {
    "std": std,
    "parkinson": parkinson,
    "garman_klass": garman_klass,
    "gk": garman_klass,
    "hodges_tompkins": hodges_tompkins,
    "ht": hodges_tompkins,
    "rogers_satchell": rogers_satchell,
    "rs": rogers_satchell,
    "yang_zhang": yang_zhang,
    "yz": yang_zhang,
    "squared_returns": squared_returns,
    "sq": squared_returns,
}


def calc_realized_volatility(
    data: pl.DataFrame | pl.LazyFrame,
    window: str = "1m",
    method: Literal[  # used to be rvol_method
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
    grouped_mean: list[int] | None = None,  # used to be rv_mean
    _trading_periods: int = 252,
    _column_name_returns: str = "log_returns",
    _column_name_close: str = "close",
    _column_name_high: str = "high",
    _column_name_low: str = "low",
    _column_name_open: str = "open",
    *,
    _sort: bool = True,
) -> pl.LazyFrame | pl.DataFrame:
    """
    Context: Toolbox || Category: Technical || **Command: calc_realized_volatility**.

    Calculates the Realized Volatility for a given time series based on the
    provided standard and extra parameters. This function adds ONE rolling
    volatility column to the input DataFrame.

    Parameters
    ----------
    data : pl.DataFrame | pl.LazyFrame
        The time series data for which to calculate the Realized Volatility.
    window : str
        The window size for a rolling volatility calculation, default is `"1m"`
        (1 month).
    method : Literal["std", "parkinson", "garman_klass", "hodges_tompkins","rogers_satchell", "yang_zhang", "squared_returns"]
        The volatility estimator to use. You can also use abbreviations to
        access the same methods. The abbreviations are: `gk` for `garman_klass`,
        `ht` for `hodges_tompkins`, `rs` for `rogers_satchell`, `yz` for
        `yang_zhang`, `sq` for `squared_returns`.
    grouped_mean : list[int] | None
        A list of window sizes to use for calculating volatility. If provided,
        the volatility method will be calculated across these various windows,
        and then an averaged value of all the windows will be returned. If `None`,
        a single window size specified by `window` parameter will be used.
    _sort : bool
        If True, the data will be sorted before calculation. Default is True.
    _trading_periods : int
        The number of trading periods in a year, default is 252 (the typical
        number of trading days in a year).
    _column_name_returns : str
        The name of the column containing the returns. Default is "log_returns".
    _column_name_close : str
        The name of the column containing the close prices. Default is "close".
    _column_name_high : str
        The name of the column containing the high prices. Default is "high".
    _column_name_low : str
        The name of the column containing the low prices. Default is "low".
    _column_name_open : str
        The name of the column containing the open prices. Default is "open".

    Returns
    -------
    VolatilityData
        The calculated Realized Volatility data for the given time series.

    Notes
    -----
    - Rolling calculations are used to show a time series of recent volatility
    that captures only a certain number of data points. The window size is
    used to determine the number of data points to use in the calculation. We do
    this because when looking at the volatility of a stock, you get a better
    insight (more granular) into the characteristics of the volatility seeing how 1-month or
    3-month rolling volatility looked over time.

    - This function does not accept `pl.Series` because the methods used to
    calculate volatility require, high, low, close, open columns for the data.
    It would be too cumbersome to pass each series needed for the calculation
    as a separate argument. Therefore, the function only accepts `pl.DataFrame`
    or `pl.LazyFrame` as input.
    """  # noqa: W505
    # Step 1: Get the correct realized volatility function =====================
    func = VOLATILITY_METHODS.get(method)
    if not func:
        msg = f"Volatility method: '{method}' is not supported."
        raise HumblDataError(msg)

    # Step 2: Get the names of the parameters that the function accepts ========
    func_params = inspect.signature(func).parameters

    # Step 3: Filter out the parameters not accepted by the function ===========
    args_to_pass = {
        key: value for key, value in locals().items() if key in func_params
    }

    # Step 4: Calculate Realized Volatility ====================================
    if grouped_mean:
        # calculate volatility over multiple windows and average the result, add to a new column
        print("🚧 WIP!")
    else:
        out = func(**args_to_pass)

    return out
