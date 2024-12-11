from typing import List

import numpy as np
import polars as pl
from openbb import obb

from humbldata.toolbox.technical.volatility.realized_volatility_helpers import (
    std,
)
from humbldata.toolbox.toolbox_controller import Toolbox


class RegimeBacktest:
    def __init__(
        self,
        symbols: list[str],
        start_date: str,
        end_date: str,
        country: str = "united_states",
        vol_window: str = "1m",
        risk_free_rate: float = 0.03,
        min_regime_days: int = 21,
    ):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.country = country
        self.vol_window = vol_window
        self.risk_free_rate = risk_free_rate
        self.min_regime_days = min_regime_days

    def get_data(self) -> tuple[pl.DataFrame, pl.DataFrame]:
        # Get COMPASS data
        toolbox = Toolbox(
            start_date=self.start_date,
            end_date=self.end_date,
            membership="admin",
        )
        compass = toolbox.fundamental.humbl_compass(
            country=self.country, z_score="3mo"
        ).to_polars()

        # Get equity data
        equity = obb.equity.price.historical(
            symbol=self.symbols,
            start_date=self.start_date,
            end_date=self.end_date,
        ).to_polars()

        return compass, equity

    def calculate_metrics(
        self, data: pl.DataFrame | pl.LazyFrame
    ) -> pl.DataFrame | pl.LazyFrame:
        """Calculate performance metrics for each regime instance"""
        return (
            data
            # First identify unique regime instances
            .with_columns(
                [
                    # Create regime instance ID when regime changes
                    (pl.col("humbl_regime") != pl.col("humbl_regime").shift())
                    .cum_sum()
                    .alias("regime_instance_id")
                ]
            )
            .with_columns(
                [
                    # Daily returns
                    (pl.col("close") / pl.col("close").shift(1) - 1).alias(
                        "daily_returns"
                    ),
                    # Log returns for volatility calculation
                    (pl.col("close") / pl.col("close").shift(1))
                    .log()
                    .alias("log_returns"),
                    # Track days in each regime instance
                    pl.col("date")
                    .count()
                    .over(["humbl_regime", "regime_instance_id"])
                    .alias("days_in_regime"),
                    # First and last prices per regime instance
                    pl.col("close")
                    .first()
                    .over(["humbl_regime", "regime_instance_id"])
                    .alias("regime_start_price"),
                    pl.col("close")
                    .last()
                    .over(["humbl_regime", "regime_instance_id"])
                    .alias("regime_end_price"),
                ]
            )
            .with_columns(
                [
                    # Total return per regime instance as percentage
                    (
                        (
                            pl.col("regime_end_price")
                            / pl.col("regime_start_price")
                            - 1
                        )
                        * 100
                    ).alias("instance_return_pct"),
                    # Annualized return (CAGR) per instance
                    (
                        (
                            pl.col("regime_end_price")
                            / pl.col("regime_start_price")
                        )
                        ** (252 / pl.col("days_in_regime"))
                        - 1
                    )
                    .mul(100)
                    .alias("instance_ann_return_pct"),
                    # Annualized volatility
                    (
                        pl.col("log_returns")
                        .rolling_std(window_size=21)
                        .mul(np.sqrt(252))
                        .mul(100)
                    ).alias("volatility_pct"),
                    # Win rate per instance
                    (pl.col("daily_returns") > 0)
                    .mean()
                    .over(["humbl_regime", "regime_instance_id"])
                    .alias("win_rate"),
                    # Risk-free rate
                    pl.lit(self.risk_free_rate).alias("risk_free_rate"),
                ]
            )
            .with_columns(
                [
                    # Sharpe Ratio per instance
                    (
                        (
                            pl.col("instance_ann_return_pct") / 100
                            - pl.col("risk_free_rate")
                        )
                        / (pl.col("volatility_pct") / 100)
                    ).alias("sharpe_ratio"),
                ]
            )
        )

    def run(self) -> pl.DataFrame:
        compass, equity = self.get_data()

        # Ensure data quality
        equity = equity.filter(pl.col("close").is_not_null()).sort("date")

        # Create daily date range from equity data
        daily_dates = equity.select(pl.col("date")).unique().sort("date")

        # Forward fill regime data to match daily equity data
        regime_data = (
            compass.select(["date_month_start", "humbl_regime"])
            .sort("date_month_start")
            # First join to get the next month's date for each regime
            .with_columns(
                pl.col("date_month_start").shift(-1).alias("next_month_start")
            )
            # Cross join with daily dates and filter to get daily regime assignments
            .join(daily_dates, how="cross")
            .filter(
                (pl.col("date") >= pl.col("date_month_start"))
                & (
                    (pl.col("date") < pl.col("next_month_start"))
                    | pl.col("next_month_start").is_null()
                )
            )
            .select(["date", "humbl_regime"])
        )

        # Merge and calculate metrics
        results = equity.join(regime_data, on="date", how="left").pipe(
            self.calculate_metrics
        )

        # Calculate summary statistics by regime
        summary = results.group_by("humbl_regime").agg(
            [
                # Average return across all instances of each regime
                pl.col("instance_return_pct")
                .mean()
                .alias("avg_total_return_pct"),
                # Average annualized return across instances
                pl.col("instance_ann_return_pct")
                .mean()
                .alias("avg_ann_return_pct"),
                # Average win rate across instances
                pl.col("win_rate").mean().alias("avg_win_rate"),
                # Average volatility
                pl.col("volatility_pct").mean().alias("avg_volatility"),
                # Average Sharpe ratio across instances
                pl.col("sharpe_ratio").mean().alias("avg_sharpe_ratio"),
                # Average days per instance
                pl.col("days_in_regime").mean().alias("avg_days_in_regime"),
                # Count of regime instances
                pl.col("regime_instance_id").n_unique().alias("instance_count"),
            ]
        )

        # Filter out regimes with too few observations
        summary = (
            summary.filter(pl.col("avg_days_in_regime") >= self.min_regime_days)
            .with_columns(
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
            .sort("regime_order")
            .drop("regime_order")
        )

        return summary
