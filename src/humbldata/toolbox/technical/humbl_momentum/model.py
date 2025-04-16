"""
**Context: Toolbox || Category: Technical || Command: momentum**.

The momentum Command Module. This module calculates various types of momentum/Rate of Change (ROC)
indicators for time series data.
"""

from typing import Literal

import polars as pl

from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.core.utils.env import Env
from humbldata.core.utils.logger import setup_logger
from humbldata.toolbox.toolbox_helpers import (
    _check_required_columns,
    _set_sort_cols,
    _window_format,
)

env = Env()
logger = setup_logger("humbl_momentum.model", level=env.LOGGER_LEVEL)


def _calc_log_roc(data: pl.LazyFrame, window_days: int = 1) -> pl.LazyFrame:
    """Calculate logarithmic rate of change."""
    try:
        # First calculate the momentum column
        data = data.with_columns(
            (pl.col("close").log() - pl.col("close").shift(window_days).log())
            .over("symbol")
            .alias("momentum")
        )

        # Then calculate the signal using the momentum column
        return data.with_columns(
            (pl.col("momentum") > 0)
            .over("symbol")
            .cast(pl.Int8)
            .alias("momentum_signal")
        )
    except Exception as e:
        logger.error(f"Error calculating log ROC: {str(e)}")
        raise HumblDataError("Failed to calculate logarithmic ROC") from e


def _calc_simple_roc(data: pl.LazyFrame, window_days: int = 1) -> pl.LazyFrame:
    """Calculate simple rate of change."""
    try:
        # First calculate the momentum column
        data = data.with_columns(
            (
                (pl.col("close") - pl.col("close").shift(window_days))
                / pl.col("close").shift(window_days)
            )
            .over("symbol")
            .alias("momentum")
        )

        # Then calculate the signal using the momentum column
        return data.with_columns(
            (pl.col("momentum") > 0)
            .over("symbol")
            .cast(pl.Int8)
            .alias("momentum_signal")
        )
    except Exception as e:
        logger.error(f"Error calculating simple ROC: {str(e)}")
        raise HumblDataError("Failed to calculate simple ROC") from e


def _calc_shift(data: pl.LazyFrame, window_days: int = 1) -> pl.LazyFrame:
    """Calculate simple time series shift."""
    try:
        # First add the shifted column
        data = data.with_columns(
            pl.col("close").shift(window_days).over("symbol").alias("shifted")
        )

        # Then calculate the signal using the shifted column
        return data.with_columns(
            (pl.col("close") > pl.col("shifted"))
            .over("symbol")
            .cast(pl.Int8)
            .alias("momentum_signal")
        )
    except Exception as e:
        logger.error(f"Error calculating shift: {str(e)}")
        raise HumblDataError("Failed to calculate shift") from e


def calc_humbl_momentum(
    data: pl.DataFrame | pl.LazyFrame,
    method: Literal["log", "simple", "shift"] = "log",
    window: str = "1d",
) -> pl.LazyFrame:
    """
    Context: Toolbox || Category: Technical || Command: calc_humbl_momentum.

    Calculate momentum/Rate of Change (ROC) for time series data.

    Parameters
    ----------
    data : pl.DataFrame | pl.LazyFrame
        Input data containing at minimum 'close' and 'date' columns
    method : Literal["log", "simple", "shift"], default "log"
        Method to calculate momentum:
        - "log": Logarithmic ROC
        - "simple": Simple ROC (percentage change)
        - "shift": Simple time series shift with binary signal
    window : str, default "1d"
        Window to calculate momentum over

    Returns
    -------
    pl.LazyFrame
        DataFrame with added columns based on method:
        - log/simple: adds 'momentum' column
        - shift: adds 'shifted' and 'momentum' columns (1 when price > shifted price, 0 otherwise)

    Raises
    ------
    HumblDataError
        If required columns are missing or calculation fails
    """
    try:
        # Validate input
        required_cols = ["close", "date"]
        _check_required_columns(data, *required_cols)
        sort_cols = _set_sort_cols(data, "symbol", "date")

        window_days: int = _window_format(
            window, _return_timedelta=True, _avg_trading_days=False
        ).days

        logger.debug(
            f"Calculating momentum using method: {method}, window: {window_days}"
        )

        # Convert to LazyFrame if DataFrame
        data = data.lazy() if isinstance(data, pl.DataFrame) else data

        # Sort by date to ensure proper shifting
        data = data.sort("date")

        # Calculate momentum based on method
        if method == "log":
            logger.debug("Using logarithmic ROC calculation")
            result = _calc_log_roc(data, window_days)
        elif method == "shift":
            logger.debug("Using simple shift calculation")
            result = _calc_shift(data, window_days)
        else:
            logger.debug("Using simple ROC calculation")
            result = _calc_simple_roc(data, window_days)

        return result.sort(sort_cols)

    except Exception as e:
        logger.error(f"Failed to calculate momentum: {str(e)}")
        raise HumblDataError(f"Momentum calculation failed: {str(e)}") from e
