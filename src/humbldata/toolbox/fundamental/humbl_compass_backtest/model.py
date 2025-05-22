"""
**Context: Toolbox || Category: Fundamental || Command: humbl_compass_backtest**.

The humbl_compass_backtest Command Module. This contains helper functions for
the transformation logic used in `HumblCompassBacktestFetcher`.

Each function corresponds to a key step in the backtest analysis process, making
the code more modular and testable.
"""

from typing import Optional

import numpy as np
import polars as pl


def forward_fill_regime_data(
    compass_data: pl.LazyFrame, equity_dates: pl.LazyFrame
) -> pl.LazyFrame:
    """
    Forward fill regime data to match daily equity data.

    Parameters
    ----------
    compass_data : pl.LazyFrame
        Compass data with date_month_start and humbl_regime columns
    equity_dates : pl.LazyFrame
        DataFrame with daily equity dates

    Returns
    -------
    pl.LazyFrame
        Daily regime data with date and humbl_regime columns
    """
    daily_regime_data = (
        compass_data.select(["date_month_start", "humbl_regime"])
        .sort("date_month_start")
        # First join to get the next month's date for each regime
        .with_columns(
            pl.col("date_month_start").shift(-1).alias("next_month_start")
        )
        # Cross join with daily dates and filter to get daily regime assignments
        .join(equity_dates, how="cross")
        .filter(
            (pl.col("date") >= pl.col("date_month_start"))
            & (
                (pl.col("date") < pl.col("next_month_start"))
                | pl.col("next_month_start").is_null()
            )
        )
        .select(["date", "humbl_regime"])
    )
    return daily_regime_data


def calculate_basic_metrics(
    equity_data: pl.LazyFrame, daily_regime_data: pl.LazyFrame
) -> pl.LazyFrame:
    """
    Calculate basic metrics for each regime instance.

    Calculates the following metrics:
    - regime_instance_id: Unique ID for each continuous regime period
    - daily_returns: Daily price returns as percentage
    - log_returns: Natural log of daily returns for volatility calculations
    - is_win_day: Boolean indicating if close price increased from previous day
    - is_loss_day: Boolean indicating if close price decreased from previous day

    Parameters
    ----------
    equity_data : pl.LazyFrame
        Equity price data
    daily_regime_data : pl.LazyFrame
        Daily regime assignments

    Returns
    -------
    pl.LazyFrame
        DataFrame with basic metrics calculated per regime instance
    """
    base_metrics = (
        equity_data.join(daily_regime_data, on="date", how="left")
        # First create regime instance ID
        .with_columns(
            (pl.col("humbl_regime") != pl.col("humbl_regime").shift())
            .cum_sum()
            .over(["symbol"])
            .alias("regime_instance_id")
        )
        # Then calculate returns within each regime instance
        .with_columns(
            [
                # Daily returns
                (pl.col("close") / pl.col("close").shift(1) - 1)
                .over(["symbol", "humbl_regime", "regime_instance_id"])
                .alias("daily_returns"),
                # Log returns for volatility calculation
                (pl.col("close") / pl.col("close").shift(1))
                .log()
                .over(["symbol", "humbl_regime", "regime_instance_id"])
                .alias("log_returns"),
                # Add win/loss indicator columns
                (pl.col("close") > pl.col("close").shift(1))
                .over(["symbol", "humbl_regime", "regime_instance_id"])
                .alias("is_win_day"),
                (pl.col("close") < pl.col("close").shift(1))
                .over(["symbol", "humbl_regime", "regime_instance_id"])
                .alias("is_loss_day"),
            ]
        )
        .drop_nulls()  # could make nulls a 0 regime_instance_id
    )
    return base_metrics


def calculate_win_loss_per_instance(base_metrics: pl.LazyFrame) -> pl.LazyFrame:
    """
    Calculate win/loss counts per regime instance.

    Parameters
    ----------
    base_metrics : pl.LazyFrame
        Base metrics data

    Returns
    -------
    pl.LazyFrame
        Win/loss counts per regime instance
    """
    return base_metrics.group_by(
        ["symbol", "humbl_regime", "regime_instance_id"]
    ).agg(
        [
            pl.col("is_win_day").sum().alias("win_days_count"),
            pl.col("is_loss_day").sum().alias("loss_days_count"),
        ]
    )


def add_regime_instance_metrics(base_metrics: pl.LazyFrame) -> pl.LazyFrame:
    """
    Add regime instance metrics to the dataframe.

    Calculates the following metrics:
    - days_in_regime: Number of days in each regime instance
    - regime_start_price: First closing price of regime instance
    - regime_end_price: Last closing price of regime instance
    - start_date: First date of regime instance
    - end_date: Last date of regime instance
    - next_day: Date following the regime instance
    - next_day_price: Closing price on the day following regime instance

    Parameters
    ----------
    base_metrics : pl.LazyFrame
        Base metrics data with date, close price and regime columns

    Returns
    -------
    pl.LazyFrame
        DataFrame with regime instance metrics added
    """
    return base_metrics.with_columns(
        [
            pl.col("date")
            .count()
            .over(["symbol", "humbl_regime", "regime_instance_id"])
            .alias("days_in_regime"),
            pl.col("close")
            .first()
            .over(["symbol", "humbl_regime", "regime_instance_id"])
            .alias("regime_start_price"),
            pl.col("close")
            .last()
            .over(["symbol", "humbl_regime", "regime_instance_id"])
            .alias("regime_end_price"),
            # Add start_date and end_date for each regime instance
            pl.col("date")
            .first()
            .over(["symbol", "humbl_regime", "regime_instance_id"])
            .alias("start_date"),
            pl.col("date")
            .last()
            .over(["symbol", "humbl_regime", "regime_instance_id"])
            .alias("end_date"),
            # Add next day for regime transition
            pl.col("date").shift(-1).over(["symbol"]).alias("next_day"),
            pl.col("close").shift(-1).over(["symbol"]).alias("next_day_price"),
        ]
    )


def calculate_performance_metrics(
    regime_metrics: pl.LazyFrame,
    volatility_window_days: int,
    risk_free_rate: float,
) -> pl.LazyFrame:
    """
    Calculate performance metrics for each regime instance.

    Calculates the following metrics:
    - instance_return_pct: Total return percentage for the regime instance
    - instance_ann_return_pct: Annualized return percentage (252 trading days)
    - volatility_pct: Annualized volatility based on rolling standard deviation
    - win_rate: Percentage of days with positive returns
    - risk_free_rate: Risk-free rate used for Sharpe ratio
    - sharpe_ratio: Risk-adjusted return measure (excess return / volatility)

    Parameters
    ----------
    regime_metrics : pl.LazyFrame
        Regime metrics data
    volatility_window_days : int
        Window size for volatility calculation
    risk_free_rate : float
        Risk-free rate used in Sharpe ratio calculation

    Returns
    -------
    pl.LazyFrame
        DataFrame with performance metrics added
    """
    performance_metrics = regime_metrics.with_columns(
        [
            # Total return
            (
                (pl.col("regime_end_price") / pl.col("regime_start_price") - 1)
                * 100
            ).alias("instance_return_pct"),
            # Annualized return
            (
                (pl.col("regime_end_price") / pl.col("regime_start_price"))
                ** (252 / pl.col("days_in_regime"))
                - 1
            )
            .mul(100)
            .alias("instance_ann_return_pct"),
            # Volatility
            pl.col("log_returns")
            .rolling_std(window_size=volatility_window_days)
            .mul(np.sqrt(252))
            .mul(100)
            .alias("volatility_pct"),
            # Win rate
            (pl.col("daily_returns") > 0)
            .mean()
            .mul(100)
            .over(["symbol", "humbl_regime", "regime_instance_id"])
            .alias("win_rate"),
            # Risk-free rate
            pl.lit(risk_free_rate).alias("risk_free_rate"),
        ]
    )

    # Add Sharpe ratio
    return performance_metrics.with_columns(
        [
            (
                (
                    pl.col("instance_ann_return_pct") / 100
                    - pl.col("risk_free_rate")
                )
                / (pl.col("volatility_pct") / 100)
            ).alias("sharpe_ratio"),
        ]
    )


def process_regime_instances(
    results: pl.LazyFrame, initial_investment: float
) -> pl.LazyFrame:
    """
    Process regime instances for investment simulation by calculating growth metrics.

    Calculates:
    - First appearance ID for each regime
    - Growth factor from instance returns
    - Cumulative growth factor within regimes
    - Investment value growth in dollars
    - Instance sequence for chronological ordering

    Parameters
    ----------
    results : pl.LazyFrame
        Results data with performance metrics
    initial_investment : float
        Initial investment amount

    Returns
    -------
    pl.LazyFrame
        Regime instances with investment growth calculated, including:
        - start_date, end_date
        - instance_return_pct
        - days_in_regime
        - next_day, next_day_price
        - regime_start_price, regime_end_price
        - growth_factor
        - cumulative_growth_factor
        - regime_investment_value
    """
    # Extract unique regime instances sorted by start date
    regime_instances = (
        results.group_by(["symbol", "humbl_regime", "regime_instance_id"])
        .agg(
            [
                pl.col("start_date").first(),
                pl.col("end_date").first(),
                pl.col("instance_return_pct").first(),
                pl.col("days_in_regime").first(),
                pl.col("next_day").first(),
                pl.col("next_day_price").first(),
                pl.col("regime_start_price").first(),
                pl.col("regime_end_price").first(),
            ]
        )
        .sort(["symbol", "start_date"])
    )

    # First, identify the first appearance of each regime per symbol
    first_regime_instances = (
        regime_instances.with_row_count("row_id")
        .group_by(["symbol", "humbl_regime"])
        .agg(pl.min("row_id").alias("first_appearance_id"))
    )

    # Join back to get all regime instances with their order per symbol
    ordered_regime_instances = (
        regime_instances.with_row_count("row_id")
        .join(first_regime_instances, on=["symbol", "humbl_regime"])
        .with_columns(
            [
                # Determine if this is the first instance of this regime
                (pl.col("row_id") == pl.col("first_appearance_id")).alias(
                    "is_first_instance"
                ),
                # Initialize investment value for each regime
                pl.lit(initial_investment).alias("initial_regime_investment"),
                # Calculate growth factor directly from instance_return_pct
                (1 + pl.col("instance_return_pct") / 100).alias(
                    "growth_factor"
                ),
                # Sort chronologically per symbol
                pl.col("start_date")
                .rank("dense")
                .over(["symbol", "humbl_regime"])
                .alias("instance_sequence"),
            ]
        )
        .sort(["symbol", "humbl_regime", "instance_sequence"])
    )

    # Calculate investment growth for all regimes in a single operation per symbol
    return ordered_regime_instances.with_columns(
        [
            # Calculate cumulative product of growth factors within each symbol and regime
            pl.col("growth_factor")
            .cum_prod()
            .over(["symbol", "humbl_regime"])
            .alias("cumulative_growth_factor"),
            # Calculate dollar value growth per symbol
            (
                pl.lit(initial_investment)
                * pl.col("growth_factor")
                .cum_prod()
                .over(["symbol", "humbl_regime"])
            ).alias("regime_investment_value"),
        ]
    )


def calculate_regime_growth(
    investment_simulation: pl.LazyFrame, initial_investment: float
) -> pl.LazyFrame:
    """
    Calculate final regime growth values and performance metrics.

    For each regime, calculates:
    - Final investment value at end of regime
    - Final cumulative growth factor
    - Total dollar growth from initial investment
    - Percentage growth from initial investment
    - Total ending investment value

    Parameters
    ----------
    investment_simulation : pl.LazyFrame
        Investment simulation results containing regime_investment_value and
        cumulative_growth_factor columns
    initial_investment : float
        Initial investment amount used as baseline for growth calculations

    Returns
    -------
    pl.LazyFrame
        Combined regime growth data with columns:
        - final_investment_value: Investment value at regime end
        - final_growth_factor: Cumulative growth factor at regime end
        - cumulative_investment_growth: Total $ growth from initial investment
        - investment_growth_pct: Total % growth from initial investment
        - total_ending_investment_value: Final investment value
    """
    return (
        investment_simulation.group_by(["symbol", "humbl_regime"])
        .agg(
            [
                pl.col("regime_investment_value")
                .last()
                .alias("final_investment_value"),
                pl.col("cumulative_growth_factor")
                .last()
                .alias("final_growth_factor"),
            ]
        )
        .with_columns(
            [
                # Calculate total growth
                (pl.col("final_investment_value") - initial_investment).alias(
                    "cumulative_investment_growth"
                ),
                # Calculate percentage growth
                (
                    (pl.col("final_investment_value") / initial_investment - 1)
                    * 100
                ).alias("investment_growth_pct"),
                # Add the total ending investment value
                pl.col("final_investment_value").alias(
                    "total_ending_investment_value"
                ),
            ]
        )
    )


def calculate_summary_statistics(
    results: pl.LazyFrame, min_regime_days: int
) -> pl.LazyFrame:
    """
    Calculate summary statistics for each regime.

    Calculates the following metrics:
    - avg_total_return_pct: Mean return across all instances of each regime
    - min_return_pct: Minimum return across all instances
    - max_return_pct: Maximum return across all instances
    - avg_ann_return_pct: Mean annualized return across instances
    - avg_win_rate_pct: Mean win rate across instances
    - avg_volatility: Mean volatility across instances
    - avg_sharpe_ratio: Mean Sharpe ratio across instances
    - avg_days_in_regime: Mean number of days per instance
    - instance_count: Total number of regime instances
    - total_win_count: Total number of winning days
    - total_loss_count: Total number of losing days
    - avg_win_count_per_instance: Mean number of winning days per instance
    - avg_loss_count_per_instance: Mean number of losing days per instance

    Parameters
    ----------
    results : pl.LazyFrame
        Results data with performance metrics
    min_regime_days : int
        Minimum number of days required for a regime to be considered valid

    Returns
    -------
    pl.LazyFrame
        Summary statistics for each regime, filtered to only include regimes
        meeting the minimum days threshold
    """
    return (
        results.group_by(["symbol", "humbl_regime"])
        .agg(
            [
                # Average return across all instances of each regime
                pl.col("instance_return_pct")
                .mean()
                .alias("avg_total_return_pct"),
                # Min and max returns across all instances
                pl.col("instance_return_pct").min().alias("min_return_pct"),
                pl.col("instance_return_pct").max().alias("max_return_pct"),
                # Average annualized return across instances
                pl.col("instance_ann_return_pct")
                .mean()
                .alias("avg_ann_return_pct"),
                # Average win rate across instances
                pl.col("win_rate").mean().alias("avg_win_rate_pct"),
                # Average volatility
                pl.col("volatility_pct").mean().alias("avg_volatility"),
                # Average Sharpe ratio across instances
                pl.col("sharpe_ratio").mean().alias("avg_sharpe_ratio"),
                # Average days per instance
                pl.col("days_in_regime").mean().alias("avg_days_in_regime"),
                # Count of regime instances
                pl.col("regime_instance_id").n_unique().alias("instance_count"),
                # Total win and loss counts
                pl.col("is_win_day").sum().alias("total_win_count"),
                pl.col("is_loss_day").sum().alias("total_loss_count"),
                # Average win and loss counts per instance
                (
                    pl.col("is_win_day").sum()
                    / pl.col("regime_instance_id").n_unique()
                ).alias("avg_win_count_per_instance"),
                (
                    pl.col("is_loss_day").sum()
                    / pl.col("regime_instance_id").n_unique()
                ).alias("avg_loss_count_per_instance"),
            ]
        )
        # Filter out regimes with too few observations
        .filter(pl.col("avg_days_in_regime") >= min_regime_days)
    )


def calculate_drawdown_metrics(base_metrics: pl.LazyFrame) -> pl.LazyFrame:
    """
    Calculate drawdown metrics for each regime.

    Calculates the following metrics:
    - running_max_price: Running maximum price within each regime instance
    - drawdown_pct: Percentage decline from running maximum price
    - is_peak: Boolean indicating if price equals running maximum
    - in_drawdown: Boolean indicating if currently in drawdown
    - drawdown_start: Boolean indicating start of new drawdown period
    - recovery_point: Boolean indicating return to peak after drawdown
    - drawdown_id: Unique identifier for each drawdown period

    For each drawdown period:
    - period_max_drawdown: Maximum percentage decline
    - period_avg_drawdown: Average percentage decline
    - drawdown_length: Number of days in drawdown
    - recovery_days: Days from drawdown start to recovery

    Final regime-level metrics:
    - max_drawdown_pct: Worst drawdown across all instances
    - avg_drawdown_pct: Average drawdown depth
    - avg_recovery_days: Average time to recover from drawdowns
    - max_recovery_days: Maximum time to recover from drawdowns

    Parameters
    ----------
    base_metrics : pl.LazyFrame
        Base metrics data

    Returns
    -------
    pl.LazyFrame
        Drawdown metrics aggregated by regime
    """
    # First, calculate running maximum and drawdowns for all data points per symbol
    metrics_with_drawdowns = base_metrics.with_columns(
        [
            # Calculate running maximum price per symbol and regime instance
            pl.col("close")
            .cum_max()
            .over(["symbol", "humbl_regime", "regime_instance_id"])
            .alias("running_max_price"),
        ]
    ).with_columns(
        [
            # Calculate drawdown percentage (negative values represent drawdowns)
            ((pl.col("close") / pl.col("running_max_price") - 1) * 100).alias(
                "drawdown_pct"
            ),
            # Identify if at peak (price equals running max)
            (pl.col("close") == pl.col("running_max_price")).alias("is_peak"),
            # Sequential day counter within each symbol and regime instance for recovery calculations
            pl.arange(1, pl.count() + 1)
            .over(["symbol", "humbl_regime", "regime_instance_id"])
            .alias("day_index"),
        ]
    )

    # Create a recovery marker - Identify start of drawdown periods and recoveries per symbol
    metrics_with_recovery = metrics_with_drawdowns.with_columns(
        [
            # In drawdown when drawdown_pct < 0
            (pl.col("drawdown_pct") < 0).alias("in_drawdown"),
            # Transition from peak to drawdown (peak at t-1, not peak at t)
            (
                pl.col("is_peak")
                .shift(1)
                .over(["symbol", "humbl_regime", "regime_instance_id"])
                & ~pl.col("is_peak")
            ).alias("drawdown_start"),
            # Recovery happens when we return to a peak after being in drawdown
            (
                ~pl.col("is_peak")
                .shift(1)
                .over(["symbol", "humbl_regime", "regime_instance_id"])
                & pl.col("is_peak")
            ).alias("recovery_point"),
        ]
    ).with_columns(
        [
            # Mark each drawdown period with unique ID per symbol
            pl.col("drawdown_start")
            .cum_sum()
            .over(["symbol", "humbl_regime", "regime_instance_id"])
            .alias("drawdown_id"),
        ]
    )

    # Calculate drawdown statistics by symbol and regime instance
    instance_drawdown_stats = (
        metrics_with_recovery.filter(
            pl.col("in_drawdown")
        )  # Only consider drawdown periods
        .group_by(
            ["symbol", "humbl_regime", "regime_instance_id", "drawdown_id"]
        )
        .agg(
            [
                # Calculate max drawdown for each drawdown period
                pl.col("drawdown_pct").min().alias("period_max_drawdown"),
                # Average drawdown for each period
                pl.col("drawdown_pct").mean().alias("period_avg_drawdown"),
                # Start day of this drawdown
                pl.col("day_index").min().alias("drawdown_start_day"),
                # Count days in drawdown
                pl.count().alias("drawdown_length"),
            ]
        )
    )

    # Mark recovery days by finding the day when each drawdown period ends
    recovery_points = (
        metrics_with_recovery.filter(pl.col("recovery_point"))
        .select(
            [
                "symbol",
                "humbl_regime",
                "regime_instance_id",
                "drawdown_id",
                "day_index",
            ]
        )
        .rename({"day_index": "recovery_day"})
    )

    # Join recovery information with drawdown stats per symbol
    drawdown_with_recovery = instance_drawdown_stats.join(
        recovery_points,
        on=["symbol", "humbl_regime", "regime_instance_id", "drawdown_id"],
        how="left",
    ).with_columns(
        [
            # Calculate recovery time (days from drawdown start to recovery)
            (pl.col("recovery_day") - pl.col("drawdown_start_day")).alias(
                "recovery_days"
            ),
        ]
    )

    # Aggregate statistics by symbol and regime
    return (
        drawdown_with_recovery.group_by(["symbol", "humbl_regime"])
        .agg(
            [
                # Worst drawdown across all instances (most negative value)
                pl.col("period_max_drawdown").min().alias("max_drawdown_pct"),
                # Average drawdown depth
                pl.col("period_avg_drawdown").mean().alias("avg_drawdown_pct"),
                # Average recovery time
                pl.col("recovery_days")
                .filter(pl.col("recovery_days").is_not_null())
                .mean()
                .alias("avg_recovery_days"),
                # Maximum recovery time
                pl.col("recovery_days")
                .filter(pl.col("recovery_days").is_not_null())
                .max()
                .alias("max_recovery_days"),
            ]
        )
        .with_columns(
            [
                # Handle null values for cases with no recovery points
                pl.col("avg_recovery_days").fill_null(0),
                pl.col("max_recovery_days").fill_null(0),
            ]
        )
    )


def calculate_win_loss_stats(
    win_loss_per_instance: pl.LazyFrame,
) -> pl.LazyFrame:
    """
    Calculate win/loss statistics for each regime.

    Calculates the following metrics:
    - max_win_days: Maximum number of winning days in any instance of the regime
    - min_win_days: Minimum number of winning days in any instance of the regime
    - max_loss_days: Maximum number of losing days in any instance of the regime
    - min_loss_days: Minimum number of losing days in any instance of the regime

    Parameters
    ----------
    win_loss_per_instance : pl.LazyFrame
        Win/loss counts per regime instance

    Returns
    -------
    pl.LazyFrame
        Win/loss statistics for each regime
    """
    return win_loss_per_instance.group_by(["symbol", "humbl_regime"]).agg(
        [
            pl.col("win_days_count").max().alias("max_win_days"),
            pl.col("win_days_count").min().alias("min_win_days"),
            pl.col("loss_days_count").max().alias("max_loss_days"),
            pl.col("loss_days_count").min().alias("min_loss_days"),
        ]
    )


def join_summary_with_win_loss(
    summary_stats: pl.LazyFrame, win_loss_stats: pl.LazyFrame
) -> pl.LazyFrame:
    """
    Join summary statistics with win/loss statistics.

    Combines regime summary statistics with win/loss metrics including:
    - max_win_days: Maximum winning days in any regime instance
    - min_win_days: Minimum winning days in any regime instance
    - max_loss_days: Maximum losing days in any regime instance
    - min_loss_days: Minimum losing days in any regime instance

    Parameters
    ----------
    summary_stats : pl.LazyFrame
        Summary statistics for each regime
    win_loss_stats : pl.LazyFrame
        Win/loss statistics for each regime

    Returns
    -------
    pl.LazyFrame
        Joined summary and win/loss statistics with all metrics combined
    """
    return summary_stats.join(
        win_loss_stats, on=["symbol", "humbl_regime"], how="left"
    )


def join_summary_with_drawdowns(
    summary_stats: pl.LazyFrame, regime_drawdowns: pl.LazyFrame
) -> pl.LazyFrame:
    """
    Join summary statistics with drawdown metrics.

    Combines regime summary statistics with drawdown metrics including:
    - max_drawdown_pct: Maximum percentage decline from peak for each regime
    - avg_drawdown_pct: Average drawdown depth across all drawdowns
    - avg_recovery_days: Average number of days to recover from drawdowns
    - max_recovery_days: Maximum number of days to recover from any drawdown

    Null values in drawdown metrics are filled with 0 since no drawdown implies
    no decline from peak.

    Parameters
    ----------
    summary_stats : pl.LazyFrame
        Summary statistics for each regime
    regime_drawdowns : pl.LazyFrame
        Drawdown metrics for each regime

    Returns
    -------
    pl.LazyFrame
        Joined summary and drawdown statistics with filled null values
    """
    return summary_stats.join(
        regime_drawdowns, on=["symbol", "humbl_regime"], how="left"
    ).with_columns(
        [
            # Fill null values with 0
            pl.col("max_drawdown_pct").fill_null(0),
            pl.col("avg_drawdown_pct").fill_null(0),
            pl.col("avg_recovery_days").fill_null(0),
            pl.col("max_recovery_days").fill_null(0),
        ]
    )


def join_summary_with_growth(
    summary_stats: pl.LazyFrame,
    combined_regime_growth: Optional[pl.LazyFrame],
    initial_investment: float,
) -> pl.LazyFrame:
    """
    Join summary statistics with investment growth data.

    Combines regime summary statistics with growth metrics including:
    - cumulative_investment_growth: Total dollar growth from initial investment
    - investment_growth_pct: Total percentage growth from initial investment
    - total_ending_investment_value: Final investment value at regime end

    If no growth data is provided, adds placeholder columns with:
    - cumulative_investment_growth: 0
    - investment_growth_pct: 0
    - total_ending_investment_value: initial_investment

    Parameters
    ----------
    summary_stats : pl.LazyFrame
        Summary statistics for each regime
    combined_regime_growth : Optional[pl.LazyFrame]
        Combined regime growth data
    initial_investment : float
        Initial investment amount

    Returns
    -------
    pl.LazyFrame
        Joined summary and growth statistics with filled null values
    """
    if combined_regime_growth is not None:
        return summary_stats.join(
            combined_regime_growth.select(
                [
                    "symbol",
                    "humbl_regime",
                    "cumulative_investment_growth",
                    "investment_growth_pct",
                    "total_ending_investment_value",
                ]
            ),
            on=["symbol", "humbl_regime"],
            how="left",
        ).with_columns(
            [
                # Fill NA values with 0 for regimes without growth data
                pl.col("cumulative_investment_growth").fill_null(0),
                pl.col("investment_growth_pct").fill_null(0),
                # Fill NA values with initial_investment for regimes without growth data
                pl.col("total_ending_investment_value").fill_null(
                    initial_investment
                ),
            ]
        )
    else:
        # If no growth data, add placeholder columns
        return summary_stats.with_columns(
            [
                pl.lit(0).alias("cumulative_investment_growth"),
                pl.lit(0).alias("investment_growth_pct"),
                pl.lit(initial_investment).alias(
                    "total_ending_investment_value"
                ),
            ]
        )


def sort_regimes(final_summary: pl.LazyFrame) -> pl.LazyFrame:
    """
    Sort regimes in correct order.

    Parameters
    ----------
    final_summary : pl.LazyFrame
        Final summary data

    Returns
    -------
    pl.LazyFrame
        Sorted final summary data
    """
    return (
        final_summary.with_columns(
            pl.col("humbl_regime")
            .replace(
                {
                    "humblBOOM": 0,
                    "humblBOUNCE": 1,
                    "humblBLOAT": 2,
                    "humblBUST": 3,
                }
            )
            .alias("regime_order")
        )
        .sort(["symbol", "regime_order"])
        .drop("regime_order")
    )


def extract_regime_date_summary(regime_metrics: pl.LazyFrame) -> pl.LazyFrame:
    """
    Extract regime date summary for visualization.

    Parameters
    ----------
    regime_metrics : pl.LazyFrame
        Regime metrics data

    Returns
    -------
    pl.LazyFrame
        Regime date summary for each regime instance
    """
    return regime_metrics.group_by(
        ["symbol", "humbl_regime", "regime_instance_id"]
    ).agg(
        [
            pl.col("start_date").first(),
            pl.col("end_date").first(),
            pl.col("days_in_regime").first(),  # Include days for context
        ]
    )


def humbl_compass_backtest(
    equity_data: pl.LazyFrame,
    compass_data: pl.LazyFrame,
    volatility_window_days: int,
    risk_free_rate: float,
    min_regime_days: int,
    initial_investment: float,
):
    """
    Context: Toolbox || Category: Fundamental ||| **Command: humbl_compass_backtest**.

    Execute the humbl_compass_backtest command by transforming equity and compass data
    into regime performance metrics.

    Parameters
    ----------
    equity_data : pl.LazyFrame
        Equity price data with date, close, and symbol columns
    compass_data : pl.LazyFrame
        Compass data with date_month_start and humbl_regime columns
    volatility_window_days : int
        Window size for volatility calculation in days
    risk_free_rate : float
        Risk-free rate used in Sharpe ratio calculation
    min_regime_days : int
        Minimum number of days required for a regime to be considered valid
    initial_investment : float
        Initial investment amount for regime growth simulation

    Returns
    -------
    tuple
        A tuple containing:
        - Final summary statistics (pl.LazyFrame)
        - Regime date summary for visualization (pl.LazyFrame)
    """
    # Step 1: Create daily date range and forward fill regime data
    daily_dates = equity_data.select(pl.col("date")).unique().sort("date")
    daily_regime_data = forward_fill_regime_data(compass_data, daily_dates)

    # Step 2: Calculate basic metrics
    base_metrics = calculate_basic_metrics(equity_data, daily_regime_data)

    # Step 3: Calculate win/loss counts per instance
    win_loss_per_instance = calculate_win_loss_per_instance(base_metrics)

    # Step 4: Add regime instance metrics
    regime_metrics = add_regime_instance_metrics(base_metrics)

    # Step 5: Calculate performance metrics
    results = calculate_performance_metrics(
        regime_metrics, volatility_window_days, risk_free_rate
    )

    # Step 6: Process regime instances for investment simulation
    investment_simulation = process_regime_instances(
        results, initial_investment
    )

    # Step 7: Calculate final regime growth values
    combined_regime_growth = calculate_regime_growth(
        investment_simulation, initial_investment
    )

    # Step 8: Calculate summary statistics
    summary_stats = calculate_summary_statistics(results, min_regime_days)

    # Step 9: Calculate win/loss statistics
    win_loss_stats = calculate_win_loss_stats(win_loss_per_instance)

    # Step 10: Calculate drawdown metrics
    regime_drawdowns = calculate_drawdown_metrics(base_metrics)

    # Step 11: Join everything together
    summary_with_win_loss = join_summary_with_win_loss(
        summary_stats, win_loss_stats
    )
    summary_with_drawdowns = join_summary_with_drawdowns(
        summary_with_win_loss, regime_drawdowns
    )
    final_summary = join_summary_with_growth(
        summary_with_drawdowns, combined_regime_growth, initial_investment
    )

    # Step 12: Sort regimes in correct order per symbol
    final_summary = sort_regimes(final_summary)

    # Step 13: Extract regime date summary for visualization
    regime_date_summary = extract_regime_date_summary(regime_metrics)

    return final_summary, regime_date_summary, daily_regime_data
