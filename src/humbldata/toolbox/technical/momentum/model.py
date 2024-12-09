"""
**Context: Toolbox || Category: Technical || Command: momentum**.

The momentum Command Module. This module calculates various types of momentum/Rate of Change (ROC)
indicators for time series data.
"""

import logging
from typing import Literal

import polars as pl

from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.toolbox.toolbox_helpers import _check_required_columns

logger = logging.getLogger(__name__)


def _calc_log_roc(data: pl.LazyFrame, period: int = 1) -> pl.LazyFrame:
    """Calculate logarithmic rate of change."""
    try:
        return data.with_columns(
            (pl.col("close").log() - pl.col("close").shift(period).log()).alias(
                "momentum"
            )
        )
    except Exception as e:
        logger.error(f"Error calculating log ROC: {str(e)}")
        raise HumblDataError("Failed to calculate logarithmic ROC") from e


def _calc_simple_roc(data: pl.LazyFrame, period: int = 1) -> pl.LazyFrame:
    """Calculate simple rate of change."""
    try:
        return data.with_columns(
            (
                (pl.col("close") - pl.col("close").shift(period))
                / pl.col("close").shift(period)
            ).alias("momentum")
        )
    except Exception as e:
        logger.error(f"Error calculating simple ROC: {str(e)}")
        raise HumblDataError("Failed to calculate simple ROC") from e


def _calc_shift(data: pl.LazyFrame, period: int = 1) -> pl.LazyFrame:
    """Calculate simple time series shift."""
    try:
        return data.with_columns(
            [
                pl.col("close").shift(period).alias("shifted"),
                (pl.col("close") > pl.col("close").shift(period))
                .cast(pl.Int8)
                .alias("momentum"),
            ]
        )
    except Exception as e:
        logger.error(f"Error calculating shift: {str(e)}")
        raise HumblDataError("Failed to calculate shift") from e


def momentum(
    data: pl.DataFrame | pl.LazyFrame,
    method: Literal["log", "simple", "shift"] = "log",
    period: int = 1,
) -> pl.LazyFrame:
    """
    Context: Toolbox || Category: Technical || Command: momentum.

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
    period : int, default 1
        Number of periods to look back for momentum calculation

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
    logger.debug(
        f"Calculating momentum using method: {method}, period: {period}"
    )

    try:
        # Validate input
        required_cols = ["close", "date"]
        _check_required_columns(data, *required_cols)

        # Convert to LazyFrame if DataFrame
        data = data.lazy() if isinstance(data, pl.DataFrame) else data

        # Sort by date to ensure proper shifting
        data = data.sort("date")

        # Calculate momentum based on method
        if method == "log":
            logger.debug("Using logarithmic ROC calculation")
            result = _calc_log_roc(data, period)
        elif method == "shift":
            logger.debug("Using simple shift calculation")
            result = _calc_shift(data, period)
        else:
            logger.debug("Using simple ROC calculation")
            result = _calc_simple_roc(data, period)

        return result.sort("date")

    except Exception as e:
        logger.error(f"Failed to calculate momentum: {str(e)}")
        raise HumblDataError(f"Momentum calculation failed: {str(e)}") from e
