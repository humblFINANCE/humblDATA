"""
HumblCompassBacktest Standard Model.

Context: Toolbox || Category: Fundamental || Command: humbl_compass_backtest.

This module is used to define the QueryParams and Data model for the
HumblCompassBacktest command.
"""

import datetime as dt
from typing import Literal, TypeVar

import numpy as np
import pandera.polars as pa
import polars as pl
import pytz
from openbb import obb
from pydantic import Field, field_validator

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.utils.env import Env
from humbldata.core.utils.logger import log_start_end, setup_logger
from humbldata.toolbox.fundamental.humbl_compass_backtest.view import (
    generate_plots,
)
from humbldata.toolbox.toolbox_helpers import _window_format

env = Env()
Q = TypeVar("Q", bound=ToolboxQueryParams)
logger = setup_logger("HumblCompassBacktestFetcher", level=env.LOGGER_LEVEL)

HUMBLCOMPASSBACKTEST_QUERY_DESCRIPTIONS = {
    "symbols": "List of stock symbols to analyze",
    "start_date": "Start date for the backtest analysis",
    "end_date": "End date for the backtest analysis",
    "country": "Country for the COMPASS analysis",
    "vol_window": "Window size for volatility calculation",
    "risk_free_rate": "Risk-free rate used in Sharpe ratio calculation",
    "min_regime_days": "Minimum number of days required for a regime to be considered valid",
    "initial_investment": "Initial investment amount for regime growth simulation",
}

CountryType = Literal[
    "g20",
    "g7",
    "asia5",
    "north_america",
    "europe4",
    "australia",
    "brazil",
    "canada",
    "china",
    "france",
    "germany",
    "india",
    "indonesia",
    "italy",
    "japan",
    "mexico",
    "south_africa",
    "south_korea",
    "spain",
    "turkey",
    "united_kingdom",
    "united_states",
    "all",
]


class HumblCompassBacktestQueryParams(QueryParams):
    """
    QueryParams model for the HumblCompassBacktest command.

    Parameters
    ----------
    symbols : List[str]
        List of stock symbols to analyze
    start_date : str
        Start date for the backtest analysis
    end_date : str
        End date for the backtest analysis
    country : CountryType, optional
        Country for the COMPASS analysis, by default "united_states"
    vol_window : str, optional
        Window size for volatility calculation, by default "1m"
    risk_free_rate : float, optional
        Risk-free rate used in Sharpe ratio calculation, by default 0.03
    min_regime_days : int, optional
        Minimum number of days required for a regime to be considered valid, by default 21
    initial_investment : float, optional
        Initial investment amount for regime growth simulation, by default 10000.0
    """

    symbols: list[str] = Field(
        default=["SPY"],
        title="Symbols",
        description=HUMBLCOMPASSBACKTEST_QUERY_DESCRIPTIONS["symbols"],
    )
    start_date: str = Field(
        default="1960-01-01",
        title="Start Date",
        description=HUMBLCOMPASSBACKTEST_QUERY_DESCRIPTIONS["start_date"],
    )
    end_date: str = Field(
        default_factory=lambda: dt.datetime.now(
            tz=pytz.timezone("America/New_York")
        )
        .date()
        .strftime("%Y-%m-%d"),
        title="End Date",
        description=HUMBLCOMPASSBACKTEST_QUERY_DESCRIPTIONS["end_date"],
    )
    country: CountryType = Field(
        default="united_states",
        title="Country",
        description=HUMBLCOMPASSBACKTEST_QUERY_DESCRIPTIONS["country"],
    )
    vol_window: str = Field(
        default="1m",
        title="Volatility Window",
        description=HUMBLCOMPASSBACKTEST_QUERY_DESCRIPTIONS["vol_window"],
    )
    risk_free_rate: float = Field(
        default=0.03,
        title="Risk-Free Rate",
        description=HUMBLCOMPASSBACKTEST_QUERY_DESCRIPTIONS["risk_free_rate"],
    )
    min_regime_days: int = Field(
        default=21,
        title="Minimum Regime Days",
        description=HUMBLCOMPASSBACKTEST_QUERY_DESCRIPTIONS["min_regime_days"],
    )
    initial_investment: float = Field(
        default=100000.0,
        title="Initial Investment",
        description=HUMBLCOMPASSBACKTEST_QUERY_DESCRIPTIONS[
            "initial_investment"
        ],
    )
    chart: bool = Field(
        default=False,
        title="Chart",
        description="Whether to generate a chart",
    )

    @field_validator("symbols")
    @classmethod
    def validate_symbols(cls, v: list[str]) -> list[str]:
        """Validate and uppercase all symbols."""
        return [symbol.upper() for symbol in v]

    @field_validator("vol_window")
    @classmethod
    def validate_vol_window(cls, v: str) -> str:
        """Validate volatility window format."""
        if v[-1] not in ["d", "w", "m", "y"]:
            msg = "vol_window must end with d, w, m, or y"
            raise ValueError(msg)
        return v.lower()


class HumblCompassBacktestData(Data):
    """
    Data model for the humbl_compass_backtest command, a Pandera.Polars Model.

    This Data model is used to validate data in the `.transform_data()` method
    of the `HumblCompassBacktestFetcher` class.

    Attributes
    ----------
    humbl_regime : pl.Utf8
        The HUMBL regime classification (BOOM, BOUNCE, BLOAT, BUST)
    avg_total_return_pct : pl.Float64
        Average total return percentage for each regime
    avg_ann_return_pct : pl.Float64
        Average annualized return percentage for each regime
    avg_win_rate_pct : pl.Float64
        Average win rate (proportion of positive returns) for each regime
    avg_volatility : pl.Float64
        Average volatility percentage for each regime
    avg_sharpe_ratio : pl.Float64
        Average Sharpe ratio for each regime
    avg_days_in_regime : pl.Float64
        Average number of days spent in each regime
    instance_count : pl.UInt32
        Number of occurrences of each regime
    cumulative_investment_growth : pl.Float64
        Cumulative growth of the initial investment amount across all instances of each regime
    investment_growth_pct : pl.Float64
        Percentage growth of investment relative to initial amount
    total_ending_investment_value : pl.Float64
        Total ending investment value including the initial investment amount
    total_win_count : pl.UInt32
        Total number of days with positive returns across all instances
    total_loss_count : pl.UInt32
        Total number of days with negative returns across all instances
    avg_win_count_per_instance : pl.Float64
        Average number of days with positive returns per instance
    avg_loss_count_per_instance : pl.Float64
        Average number of days with negative returns per instance
    min_return_pct : pl.Float64
        Minimum return percentage across all instances of the regime
    max_return_pct : pl.Float64
        Maximum return percentage across all instances of the regime
    max_win_days : pl.UInt32
        Maximum number of win days in any instance of the regime
    min_win_days : pl.UInt32
        Minimum number of win days in any instance of the regime
    max_loss_days : pl.UInt32
        Maximum number of loss days in any instance of the regime
    min_loss_days : pl.UInt32
        Minimum number of loss days in any instance of the regime
    max_drawdown_pct : pl.Float64
        Maximum drawdown percentage across all instances of the regime
    avg_drawdown_pct : pl.Float64
        Average drawdown percentage across all instances of the regime
    avg_recovery_days : pl.Float64
        Average number of days to recover from drawdowns
    max_recovery_days : pl.UInt32
        Maximum number of days to recover from drawdowns
    """

    humbl_regime: pl.Utf8 = pa.Field(
        title="HUMBL Regime",
        description="The HUMBL regime classification (BOOM, BOUNCE, BLOAT, BUST)",
    )
    avg_total_return_pct: pl.Float64 = pa.Field(
        title="Average Total Return %",
        description="Average total return percentage for each regime",
    )
    avg_ann_return_pct: pl.Float64 = pa.Field(
        title="Average Annualized Return %",
        description="Average annualized return percentage for each regime",
    )
    avg_win_rate_pct: pl.Float64 = pa.Field(
        title="Average Win Rate %",
        description="Average win rate (proportion of positive returns) for each regime",
    )
    avg_volatility: pl.Float64 = pa.Field(
        title="Average Volatility",
        description="Average volatility percentage for each regime",
    )
    avg_sharpe_ratio: pl.Float64 = pa.Field(
        title="Average Sharpe Ratio",
        description="Average Sharpe ratio for each regime",
    )
    avg_days_in_regime: pl.Float64 = pa.Field(
        title="Average Days in Regime",
        description="Average number of days spent in each regime",
    )
    instance_count: pl.UInt32 = pa.Field(
        title="Instance Count",
        description="Number of occurrences of each regime",
    )
    cumulative_investment_growth: pl.Float64 = pa.Field(
        title="Cumulative Investment Growth",
        description="Cumulative growth of the initial investment amount across all instances of each regime",
    )
    investment_growth_pct: pl.Float64 = pa.Field(
        title="Investment Growth %",
        description="Percentage growth of investment relative to initial amount",
    )
    total_ending_investment_value: pl.Float64 = pa.Field(
        title="Total Ending Investment Value",
        description="Total ending investment value including the initial investment amount",
    )
    total_win_count: pl.UInt32 = pa.Field(
        title="Total Win Count",
        description="Total number of days with positive returns across all instances",
    )
    total_loss_count: pl.UInt32 = pa.Field(
        title="Total Loss Count",
        description="Total number of days with negative returns across all instances",
    )
    avg_win_count_per_instance: pl.Float64 = pa.Field(
        title="Avg Win Count Per Instance",
        description="Average number of days with positive returns per instance",
    )
    avg_loss_count_per_instance: pl.Float64 = pa.Field(
        title="Avg Loss Count Per Instance",
        description="Average number of days with negative returns per instance",
    )
    min_return_pct: pl.Float64 = pa.Field(
        title="Min Return %",
        description="Minimum return percentage across all instances of the regime",
    )
    max_return_pct: pl.Float64 = pa.Field(
        title="Max Return %",
        description="Maximum return percentage across all instances of the regime",
    )
    max_win_days: pl.UInt32 = pa.Field(
        title="Max Win Days",
        description="Maximum number of win days in any instance of the regime",
    )
    min_win_days: pl.UInt32 = pa.Field(
        title="Min Win Days",
        description="Minimum number of win days in any instance of the regime",
    )
    max_loss_days: pl.UInt32 = pa.Field(
        title="Max Loss Days",
        description="Maximum number of loss days in any instance of the regime",
    )
    min_loss_days: pl.UInt32 = pa.Field(
        title="Min Loss Days",
        description="Minimum number of loss days in any instance of the regime",
    )
    max_drawdown_pct: pl.Float64 = pa.Field(
        title="Max Drawdown %",
        description="Maximum drawdown percentage across all instances of the regime",
    )
    avg_drawdown_pct: pl.Float64 = pa.Field(
        title="Avg Drawdown %",
        description="Average drawdown percentage across all instances of the regime",
    )
    avg_recovery_days: pl.Float64 = pa.Field(
        title="Avg Recovery Days",
        description="Average number of days to recover from drawdowns",
    )
    max_recovery_days: pl.Int64 = pa.Field(
        title="Max Recovery Days",
        description="Maximum number of days to recover from drawdowns",
    )


class HumblCompassBacktestFetcher:
    """
    Fetcher for the HumblCompassBacktest command.

    Parameters
    ----------
    context_params : ToolboxQueryParams
        The context parameters for the Toolbox query.
    command_params : HumblCompassBacktestQueryParams
        The command-specific parameters for the HumblCompassBacktest query.

    Attributes
    ----------
    context_params : ToolboxQueryParams
        Stores the context parameters passed during initialization.
    command_params : HumblCompassBacktestQueryParams
        Stores the command-specific parameters passed during initialization.
    data : pl.DataFrame
        The raw data extracted from the data provider, before transformation.
    warnings : List[Warning_]
        List of warnings generated during data processing.
    extra : dict
        Additional metadata or results from data processing.
    chart : Optional[Chart]
        Optional chart object for visualization.

    Methods
    -------
    transform_query()
        Transform the command-specific parameters into a query.
    extract_data()
        Extracts the data from the provider and returns it as a Polars DataFrame.
    transform_data()
        Transforms the command-specific data according to the HumblCompassBacktest logic.
    fetch_data()
        Execute TET Pattern.

    Returns
    -------
    HumblObject
        results : HumblCompassBacktestData
            Serializable results.
        provider : Literal['fmp', 'intrinio', 'polygon', 'tiingo', 'yfinance']
            Provider name.
        warnings : List[Warning_]
            List of warnings from both context and command.
        chart : Optional[Chart]
            Chart object.
        context_params : ToolboxQueryParams
            Context-specific parameters.
        command_params : HumblCompassBacktestQueryParams
            Command-specific parameters.
        extra : dict
            Additional metadata or results.
    """

    def __init__(
        self,
        context_params: ToolboxQueryParams,
        command_params: HumblCompassBacktestQueryParams,
        compass_data: pl.DataFrame | pl.LazyFrame | None = None,
    ):
        """
        Initialize the HumblCompassBacktestFetcher with context and command parameters.

        Parameters
        ----------
        context_params : ToolboxQueryParams
            The context parameters for the Toolbox query.
        command_params : HumblCompassBacktestQueryParams
            The command-specific parameters for the HumblCompassBacktest query.
        compass_data : pl.DataFrame | None
            Optional pre-computed compass data to use instead of fetching it.
        """
        self.context_params = context_params
        self.command_params = command_params
        self.compass_data = compass_data
        self.warnings = []
        self.extra = {}
        self.chart = None

    def transform_query(self):
        """
        Transform the command-specific parameters into a query.

        If command_params is not provided, it initializes a default
        HumblCompassBacktestQueryParams object.
        """
        if not isinstance(self.command_params, HumblCompassBacktestQueryParams):
            if self.command_params:
                self.command_params = HumblCompassBacktestQueryParams(
                    **self.command_params
                )
            else:
                self.command_params = HumblCompassBacktestQueryParams()

    def extract_data(self):
        """
        Extract the data from the provider and returns it as a Polars DataFrame.

        Returns
        -------
        self
            Returns self for method chaining.
        """
        # Use existing compass data if provided
        if self.compass_data is None:
            # Import here to avoid circular import
            from humbldata.core.standard_models.toolbox.fundamental.humbl_compass import (
                HumblCompassFetcher,
                HumblCompassQueryParams,
            )

            # Get compass data through the proper fetcher
            compass_params = HumblCompassQueryParams(
                country=self.command_params.country,
            )
            compass_fetcher = HumblCompassFetcher(
                self.context_params, compass_params
            )
            compass_results = compass_fetcher.fetch_data()
            self.humbl_compass_data = compass_results.to_polars(collect=True)
        else:
            self.humbl_compass_data = self.compass_data

        # Get equity data
        equity_data = obb.equity.price.historical(
            symbol=self.command_params.symbols,
            start_date=self.command_params.start_date,
            end_date=self.command_params.end_date,
            provider="yfinance",
        )
        self.equity_data = equity_data.to_polars().lazy()

        if len(self.command_params.symbols) == 1:
            self.equity_data = self.equity_data.with_columns(
                symbol=pl.lit(self.command_params.symbols[0])
            )
        return self

    def transform_data(self):
        """
        Transform raw data into regime backtest metrics.

        Returns
        -------
        self
            Returns self for method chaining.
        """
        equity = self.equity_data.lazy()
        compass = self.humbl_compass_data.lazy()

        window_format_result = _window_format(
            self.command_params.vol_window,
            _return_timedelta=True,
            _avg_trading_days=True,
        )
        # Extract days safely (assuming _window_format returns an object with days attribute)
        if hasattr(window_format_result, "days"):
            window_days = window_format_result.days
        else:
            # Default fallback if days attribute not available
            window_days = 21  # Default to 21 days (approximately 1 month)
            self.warnings.append(
                "Could not determine window days, using default of 21 days"
            )

        # Step 1: Create daily date range
        daily_dates = equity.select(pl.col("date")).unique().sort("date")

        # Forward fill regime data to match daily equity data
        daily_regime_data = (
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

        # Step 4: Calculate basic metrics
        base_metrics = (
            equity.join(daily_regime_data, on="date", how="left")
            # First create regime instance ID
            .with_columns(
                (pl.col("humbl_regime") != pl.col("humbl_regime").shift())
                .cum_sum()
                .alias("regime_instance_id")
            )
            # Then calculate returns within each regime instance
            .with_columns(
                [
                    # Daily returns
                    (pl.col("close") / pl.col("close").shift(1) - 1)
                    .over(["humbl_regime", "regime_instance_id"])
                    .alias("daily_returns"),
                    # Log returns for volatility calculation
                    (pl.col("close") / pl.col("close").shift(1))
                    .log()
                    .over(["humbl_regime", "regime_instance_id"])
                    .alias("log_returns"),
                    # Add win/loss indicator columns
                    (pl.col("close") > pl.col("close").shift(1))
                    .over(["humbl_regime", "regime_instance_id"])
                    .alias("is_win_day"),
                    (pl.col("close") < pl.col("close").shift(1))
                    .over(["humbl_regime", "regime_instance_id"])
                    .alias("is_loss_day"),
                ]
            )
            .drop_nulls()  # could make nulls a 0 regime_instance_id
        )

        # Calculate win/loss counts per instance for min/max aggregation
        win_loss_per_instance = base_metrics.group_by(
            ["humbl_regime", "regime_instance_id"]
        ).agg(
            [
                pl.col("is_win_day").sum().alias("win_days_count"),
                pl.col("is_loss_day").sum().alias("loss_days_count"),
            ]
        )

        # Step 5: Add regime instance metrics
        regime_metrics = base_metrics.with_columns(
            [
                pl.col("date")
                .count()
                .over(["humbl_regime", "regime_instance_id"])
                .alias("days_in_regime"),
                pl.col("close")
                .first()
                .over(["humbl_regime", "regime_instance_id"])
                .alias("regime_start_price"),
                pl.col("close")
                .last()
                .over(["humbl_regime", "regime_instance_id"])
                .alias("regime_end_price"),
                # Add start_date and end_date for each regime instance
                pl.col("date")
                .first()
                .over(["humbl_regime", "regime_instance_id"])
                .alias("start_date"),
                pl.col("date")
                .last()
                .over(["humbl_regime", "regime_instance_id"])
                .alias("end_date"),
                # Add next day for regime transition
                pl.col("date").shift(-1).over(["symbol"]).alias("next_day"),
                pl.col("close")
                .shift(-1)
                .over(["symbol"])
                .alias("next_day_price"),
            ]
        )

        # Step 6: Calculate performance metrics
        performance_metrics = regime_metrics.with_columns(
            [
                # Total return
                (
                    (
                        pl.col("regime_end_price")
                        / pl.col("regime_start_price")
                        - 1
                    )
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
                .rolling_std(window_size=window_days)
                .mul(np.sqrt(252))
                .mul(100)
                .alias("volatility_pct"),
                # Win rate
                (pl.col("daily_returns") > 0)
                .mean()
                .mul(100)
                .over(["humbl_regime", "regime_instance_id"])
                .alias("win_rate"),
                # Risk-free rate
                pl.lit(self.command_params.risk_free_rate).alias(
                    "risk_free_rate"
                ),
            ]
        )

        # Step 7: Add Sharpe ratio
        results = performance_metrics.with_columns(
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

        # Step 8: Process regime instances for investment simulation
        # Extract unique regime instances sorted by start date
        regime_instances = (
            results.group_by(["humbl_regime", "regime_instance_id"])
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
            .sort(["start_date"])
        )

        # Calculate investment growth for each regime
        initial_investment = self.command_params.initial_investment

        # First, identify the first appearance of each regime
        first_regime_instances = (
            regime_instances.with_row_count("row_id")
            .group_by("humbl_regime")
            .agg(pl.min("row_id").alias("first_appearance_id"))
        )

        # Join back to get all regime instances with their order
        ordered_regime_instances = (
            regime_instances.with_row_count("row_id")
            .join(first_regime_instances, on="humbl_regime")
            .with_columns(
                # Determine if this is the first instance of this regime
                (pl.col("row_id") == pl.col("first_appearance_id")).alias(
                    "is_first_instance"
                ),
                # Initialize investment value for each regime
                pl.lit(initial_investment).alias("initial_regime_investment"),
            )
        )

        # Calculate investment growth simulation
        # We'll do this by processing regimes in chronological order
        investment_simulation = ordered_regime_instances.sort(
            "start_date"
        ).with_columns(
            [
                # Calculate growth factor directly from instance_return_pct
                (1 + pl.col("instance_return_pct") / 100).alias(
                    "growth_factor"
                ),
                # Assign regime order for tracking growth across instances
                pl.col("row_id")
                .rank("dense")
                .alias("regime_chronological_order"),
            ]
        )

        # Calculate cumulative investment values for each regime independently
        regimes = ["humblBOOM", "humblBOUNCE", "humblBLOAT", "humblBUST"]

        # Process each regime's investment growth independently
        regime_growth_frames = []

        for regime in regimes:
            # Filter for just this regime
            regime_data = investment_simulation.filter(
                pl.col("humbl_regime") == regime
            )

            if (
                regime_data.collect().height > 0
            ):  # Check if this regime exists in data
                # Calculate cumulative growth for this regime
                regime_growth = regime_data.with_columns(
                    # Current investment = previous investment * growth factor
                    pl.col("growth_factor")
                    .cum_prod()
                    .over("humbl_regime")
                    .alias("cumulative_growth_factor"),
                    # Calculate dollar value growth
                    (
                        pl.lit(initial_investment)
                        * pl.col("growth_factor")
                        .cum_prod()
                        .over("humbl_regime")
                    ).alias("regime_investment_value"),
                )

                # Get final growth values for this regime
                regime_final_growth = (
                    regime_growth.group_by("humbl_regime")
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
                            (
                                pl.col("final_investment_value")
                                - initial_investment
                            ).alias("cumulative_investment_growth"),
                            (
                                (
                                    pl.col("final_investment_value")
                                    / initial_investment
                                    - 1
                                )
                                * 100
                            ).alias("investment_growth_pct"),
                            # Add the total ending investment value
                            pl.col("final_investment_value").alias(
                                "total_ending_investment_value"
                            ),
                        ]
                    )
                )

                regime_growth_frames.append(regime_final_growth)

        # Combine all regime growth data
        combined_regime_growth = (
            pl.concat(regime_growth_frames).lazy()
            if regime_growth_frames
            else None
        )

        # Step 9: Calculate final summary statistics
        summary_stats = (
            results.group_by("humbl_regime")
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
                    pl.col("regime_instance_id")
                    .n_unique()
                    .alias("instance_count"),
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
            .filter(
                pl.col("avg_days_in_regime")
                >= self.command_params.min_regime_days
            )
        )

        # Calculate drawdown metrics using vectorized operations
        # First, calculate running maximum and drawdowns for all data points
        metrics_with_drawdowns = base_metrics.with_columns(
            [
                # Calculate running maximum price per regime instance
                pl.col("close")
                .cum_max()
                .over(["humbl_regime", "regime_instance_id"])
                .alias("running_max_price"),
            ]
        ).with_columns(
            [
                # Calculate drawdown percentage (negative values represent drawdowns)
                (
                    (pl.col("close") / pl.col("running_max_price") - 1) * 100
                ).alias("drawdown_pct"),
                # Identify if at peak (price equals running max)
                (pl.col("close") == pl.col("running_max_price")).alias(
                    "is_peak"
                ),
                # Sequential day counter within each regime instance for recovery calculations
                pl.arange(1, pl.count() + 1)
                .over(["humbl_regime", "regime_instance_id"])
                .alias("day_index"),
            ]
        )

        # Create a recovery marker - Identify start of drawdown periods and recoveries
        # A new drawdown starts when we fall from a peak
        metrics_with_recovery = metrics_with_drawdowns.with_columns(
            [
                # In drawdown when drawdown_pct < 0
                (pl.col("drawdown_pct") < 0).alias("in_drawdown"),
                # Transition from peak to drawdown (peak at t-1, not peak at t)
                (
                    pl.col("is_peak")
                    .shift(1)
                    .over(["humbl_regime", "regime_instance_id"])
                    & ~pl.col("is_peak")
                ).alias("drawdown_start"),
                # Recovery happens when we return to a peak after being in drawdown
                (
                    ~pl.col("is_peak")
                    .shift(1)
                    .over(["humbl_regime", "regime_instance_id"])
                    & pl.col("is_peak")
                ).alias("recovery_point"),
            ]
        ).with_columns(
            [
                # Mark each drawdown period with unique ID
                pl.col("drawdown_start")
                .cum_sum()
                .over(["humbl_regime", "regime_instance_id"])
                .alias("drawdown_id"),
            ]
        )

        # Calculate drawdown statistics by regime instance
        instance_drawdown_stats = (
            metrics_with_recovery.filter(
                pl.col("in_drawdown")
            )  # Only consider drawdown periods
            .group_by(["humbl_regime", "regime_instance_id", "drawdown_id"])
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
                    "humbl_regime",
                    "regime_instance_id",
                    "drawdown_id",
                    "day_index",
                ]
            )
            .rename({"day_index": "recovery_day"})
        )

        # Join recovery information with drawdown stats
        drawdown_with_recovery = instance_drawdown_stats.join(
            recovery_points,
            on=["humbl_regime", "regime_instance_id", "drawdown_id"],
            how="left",
        ).with_columns(
            [
                # Calculate recovery time (days from drawdown start to recovery)
                (pl.col("recovery_day") - pl.col("drawdown_start_day")).alias(
                    "recovery_days"
                ),
            ]
        )

        # Aggregate statistics by regime
        regime_drawdowns = (
            drawdown_with_recovery.group_by("humbl_regime")
            .agg(
                [
                    # Worst drawdown across all instances (most negative value)
                    pl.col("period_max_drawdown")
                    .min()
                    .alias("max_drawdown_pct"),
                    # Average drawdown depth
                    pl.col("period_avg_drawdown")
                    .mean()
                    .alias("avg_drawdown_pct"),
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

        # Ensure all regimes are included, even if they don't have drawdowns
        missing_regimes = set(regimes) - set(
            regime_drawdowns.collect()["humbl_regime"]
        )
        if missing_regimes:
            # Create placeholder dataframe for missing regimes
            missing_df = pl.DataFrame(
                {
                    "humbl_regime": list(missing_regimes),
                    "max_drawdown_pct": [0.0] * len(missing_regimes),
                    "avg_drawdown_pct": [0.0] * len(missing_regimes),
                    "avg_recovery_days": [0.0] * len(missing_regimes),
                    "max_recovery_days": [0] * len(missing_regimes),
                }
            )

            # Combine with existing drawdown results
            regime_drawdowns = pl.concat([regime_drawdowns, missing_df]).lazy()

        # Get min/max win/loss days per regime
        win_loss_stats = win_loss_per_instance.group_by("humbl_regime").agg(
            [
                pl.col("win_days_count").max().alias("max_win_days"),
                pl.col("win_days_count").min().alias("min_win_days"),
                pl.col("loss_days_count").max().alias("max_loss_days"),
                pl.col("loss_days_count").min().alias("min_loss_days"),
            ]
        )

        # Join with summary stats
        summary_stats = summary_stats.join(
            win_loss_stats, on="humbl_regime", how="left"
        )

        # Join drawdown statistics
        summary_stats = summary_stats.join(
            regime_drawdowns, on="humbl_regime", how="left"
        ).with_columns(
            [
                # Fill null values with 0
                pl.col("max_drawdown_pct").fill_null(0),
                pl.col("avg_drawdown_pct").fill_null(0),
                pl.col("avg_recovery_days").fill_null(0),
                pl.col("max_recovery_days").fill_null(0),
            ]
        )

        # Join investment growth data to summary stats
        if combined_regime_growth is not None:
            final_summary = summary_stats.join(
                combined_regime_growth.select(
                    [
                        "humbl_regime",
                        "cumulative_investment_growth",
                        "investment_growth_pct",
                        "total_ending_investment_value",
                    ]
                ),
                on="humbl_regime",
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
            final_summary = summary_stats.with_columns(
                [
                    pl.lit(0).alias("cumulative_investment_growth"),
                    pl.lit(0).alias("investment_growth_pct"),
                    pl.lit(initial_investment).alias(
                        "total_ending_investment_value"
                    ),
                ]
            )

        # Step 10: Sort regimes in correct order
        final_summary = (
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
            .sort("regime_order")
            .drop("regime_order")
        )

        # Step 11: Extract regime date summary
        # Aggregate to get one row per regime instance
        regime_date_summary = regime_metrics.group_by(
            ["humbl_regime", "regime_instance_id", "symbol"]
        ).agg(
            [
                pl.col("start_date").first(),
                pl.col("end_date").first(),
                pl.col("days_in_regime").first(),  # Include days for context
            ]
        )

        if self.command_params.chart:
            self.chart = generate_plots(self.equity_data, regime_date_summary)
        # Store transformed data
        self.transformed_data = (
            HumblCompassBacktestData(final_summary)
            .lazy()
            .serialize(format="binary")
        )
        self.equity_data = self.equity_data.serialize(format="binary")
        self.extra["daily_regime_data"] = daily_regime_data.lazy()

        return self

    @log_start_end(logger=logger)
    def fetch_data(self):
        """
        Execute TET Pattern.

        This method executes the query transformation, data fetching and
        transformation process by first calling `transform_query` to prepare the query parameters, then
        extracting the raw data using `extract_data` method, and finally
        transforming the raw data using `transform_data` method.

        Returns
        -------
        HumblObject
            The HumblObject containing the transformed data and metadata.
        """
        logger.debug("Running .transform_query()")
        self.transform_query()
        logger.debug("Running .extract_data()")
        self.extract_data()
        logger.debug("Running .transform_data()")
        self.transform_data()

        # Initialize extra dict if it doesn't exist
        if not hasattr(self, "extra"):
            self.extra = {}

        # Use context params warnings if available, otherwise initialize empty list
        context_warnings = getattr(self.context_params, "warnings", [])

        # Combine warnings
        all_warnings = context_warnings + self.warnings

        return HumblObject(
            results=self.transformed_data,
            provider=self.context_params.provider,
            equity_data=self.equity_data,
            warnings=all_warnings,
            chart=self.chart,
            context_params=self.context_params,
            command_params=self.command_params,
            extra=self.extra,
        )
