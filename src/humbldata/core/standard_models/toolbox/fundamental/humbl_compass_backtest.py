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
from humbldata.toolbox.fundamental.humbl_compass_backtest.model import (
    humbl_compass_backtest,
)
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
    symbol : pl.Utf8
        The stock symbol being analyzed
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

    symbol: pl.Utf8 = pa.Field(
        title="Symbol",
        description="The stock symbol being analyzed",
    )
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
            provider=self.context_params.provider,
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
        equity_data = self.equity_data.lazy()
        compass_data = self.humbl_compass_data.lazy()

        volatility_window_days = _window_format(
            self.command_params.vol_window,
            _return_timedelta=True,
            _avg_trading_days=True,
        ).days

        final_summary, regime_date_summary, daily_regime_data = (
            humbl_compass_backtest(
                equity_data=equity_data,
                compass_data=compass_data,
                volatility_window_days=volatility_window_days,
                risk_free_rate=self.command_params.risk_free_rate,
                min_regime_days=self.command_params.min_regime_days,
                initial_investment=self.command_params.initial_investment,
            )
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
