"""
HumblCompassBacktest Standard Model.

Context: Toolbox || Category: Fundamental || Command: humbl_compass_backtest.

This module is used to define the QueryParams and Data model for the
HumblCompassBacktest command.
"""

import datetime as dt
from typing import TypeVar

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
}


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
    country : str, optional
        Country for the COMPASS analysis, by default "united_states"
    vol_window : str, optional
        Window size for volatility calculation, by default "1m"
    risk_free_rate : float, optional
        Risk-free rate used in Sharpe ratio calculation, by default 0.03
    min_regime_days : int, optional
        Minimum number of days required for a regime to be considered valid, by default 21
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
    country: str = Field(
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
        self.equity_data = (
            obb.equity.price.historical(
                symbol=self.command_params.symbols,
                start_date=self.command_params.start_date,
                end_date=self.command_params.end_date,
                provider="yfinance",
            )
            .to_polars()
            .lazy()
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

        window_days = _window_format(
            self.command_params.vol_window,
            _return_timedelta=True,
            _avg_trading_days=True,
        ).days

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
                ]
            )
            .drop_nulls()
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

        # Step 8: Calculate final summary statistics
        summary_stats = (
            results.group_by("humbl_regime")
            .agg(
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
                ]
            )
            # Filter out regimes with too few observations
            .filter(
                pl.col("avg_days_in_regime")
                >= self.command_params.min_regime_days
            )
        )

        # Step 9: Sort regimes in correct order
        final_summary = (
            summary_stats.with_columns(
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

        # Store transformed data
        self.transformed_data = (
            HumblCompassBacktestData(final_summary)
            .lazy()
            .serialize(format="binary")
        )
        self.equity_data = self.equity_data.serialize(format="binary")
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

        # Initialize warnings list if it doesn't exist
        if not hasattr(self.context_params, "warnings"):
            self.context_params.warnings = []

        # Initialize fetcher warnings if they don't exist
        if not hasattr(self, "warnings"):
            self.warnings = []

        # Initialize extra dict if it doesn't exist
        if not hasattr(self, "extra"):
            self.extra = {}

        # Combine warnings from both sources
        all_warnings = self.context_params.warnings + self.warnings

        return HumblObject(
            results=self.transformed_data,
            provider=self.context_params.provider,
            equity_data=self.equity_data,
            warnings=all_warnings,  # Use combined warnings
            chart=self.chart,
            context_params=self.context_params,
            command_params=self.command_params,
            extra=self.extra,  # pipe in extra from transform_data()
        )
