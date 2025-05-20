"""
HumblCompass Standard Model.

Context: Toolbox || Category: Fundamental || Command: humbl_compass.

This module is used to define the QueryParams and Data model for the
HumblCompass command.
"""

import warnings
from datetime import datetime
from enum import Enum
from typing import Literal, TypeVar

import pandera.polars as pa
import polars as pl
from aiocache import RedisCache, cached
from pydantic import BaseModel, Field

from humbldata.core.standard_models.abstract.chart import ChartTemplate
from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.abstract.warnings import (
    HumblDataWarning,
    collect_warnings,
)
from humbldata.core.standard_models.openbbapi.EconomyCompositeLeadingIndicatorQueryParams import (
    EconomyCompositeLeadingIndicatorQueryParams,
)
from humbldata.core.standard_models.openbbapi.EconomyConsumerPriceIndexQueryParams import (
    EconomyConsumerPriceIndexQueryParams,
)
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.utils.cache import (
    CustomPickleSerializer,
    LogCacheHitPlugin,
    build_cache_key,
    get_redis_cache_config,
)
from humbldata.core.utils.core_helpers import serialize_lazyframe_to_ipc
from humbldata.core.utils.env import Env
from humbldata.core.utils.logger import log_start_end, setup_logger
from humbldata.core.utils.openbb_api_client import OpenBBAPIClient
from humbldata.toolbox.fundamental.humbl_compass.view import generate_plots
from humbldata.toolbox.toolbox_helpers import (
    _window_format,
    _window_format_monthly,
)

env = Env()
Q = TypeVar("Q", bound=ToolboxQueryParams)
logger = setup_logger("HumblCompassFetcher", level=env.LOGGER_LEVEL)


# Custom cache key builder (mimics previous logic)
def humbl_compass_key_builder(func, self, *args, **kwargs):
    """Build cache key for HumblCompass data."""
    return build_cache_key(self, command_param_fields=["country", "z_score"])


HUMBLCOMPASS_QUERY_DESCRIPTIONS = {
    "example_field1": "Description for example field 1",
    "example_field2": "Description for example field 2",
    "chart": "Whether to return a chart object.",
    "template": "The template/theme to use for the plotly figure.",
}

HUMBLCOMPASS_DATA_DESCRIPTIONS = {
    "date": "The date of the data point",
    "country": "The country or group of countries the data represents",
    "cpi": "Consumer Price Index (CPI) value",
    "cpi_3m_delta": "3-month delta of CPI",
    "cpi_1yr_zscore": "1-year rolling z-score of CPI",
    "cli": "Composite Leading Indicator (CLI) value",
    "cli_3m_delta": "3-month delta of CLI",
    "cli_1yr_zscore": "1-year rolling z-score of CLI",
    "humbl_regime": "HUMBL Regime classification based on CPI and CLI values",
}


class AssetRecommendation(str, Enum):
    """Asset recommendation categories."""

    EQUITIES = "Equities"
    CREDIT = "Credit"
    COMMODITIES = "Commodities"
    FX = "FX"
    FIXED_INCOME = "Fixed Income"
    USD = "USD"
    GOLD = "Gold"
    TECHNOLOGY = "Technology"
    CONSUMER_DISCRETIONARY = "Consumer Discretionary"
    MATERIALS = "Materials"
    INDUSTRIALS = "Industrials"
    UTILITIES = "Utilities"
    REITS = "REITs"
    CONSUMER_STAPLES = "Consumer Staples"
    FINANCIALS = "Financials"
    ENERGY = "Energy"
    HEALTH_CARE = "Health Care"
    TELECOM = "Telecom"
    HIGH_BETA = "High Beta"
    MOMENTUM = "Momentum"
    CYCLICALS = "Cyclicals"
    SECULAR_GROWTH = "Secular Growth"
    LOW_BETA = "Low Beta"
    DEFENSIVES = "Defensives"
    VALUE = "Value"
    DIVIDEND_YIELD = "Dividend Yield"
    QUALITY = "Quality"
    CYCLICAL_GROWTH = "Cyclical Growth"
    SMALL_CAPS = "Small Caps"
    MID_CAPS = "Mid Caps"
    BDCS = "BDCs"
    CONVERTIBLES = "Convertibles"
    HY_CREDIT = "HY Credit"
    EM_DEBT = "EM Debt"
    TIPS = "TIPS"
    SHORT_DURATION_TREASURIES = "Short Duration Treasuries"
    MORTGAGE_BACKED_SECURITIES = "Mortgage Backed Securities"
    MEDIUM_DURATION_TREASURIES = "Medium Duration Treasuries"
    LONG_DURATION_TREASURIES = "Long Duration Treasuries"
    IG_CREDIT = "Investment Grade Credit"
    MUNIS = "Municipal Bonds"
    PREFERREDS = "Preferreds"
    EM_LOCAL_CURRENCY = "Emerging Market Local Currency"
    LEVERAGED_LOANS = "Leveraged Loans"


class RecommendationCategory(BaseModel):
    """Category-specific recommendations with rationale."""

    best: list[AssetRecommendation]
    worst: list[AssetRecommendation]
    rationale: str


class RegimeRecommendations(BaseModel):
    """Complete set of recommendations for a specific regime."""

    asset_classes: RecommendationCategory
    equity_sectors: RecommendationCategory
    equity_factors: RecommendationCategory
    fixed_income: RecommendationCategory
    regime_description: str
    key_risks: list[str]
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class HumblCompassQueryParams(QueryParams):
    """
    QueryParams model for the HumblCompass command, a Pydantic v2 model.

    Parameters
    ----------
    country : Literal
        The country or group of countries to collect humblCOMPASS data for.
    cli_start_date : str
        The adjusted start date for CLI data collection.
    cpi_start_date : str
        The adjusted start date for CPI data collection.
    z_score : Optional[str]
        The time window for z-score calculation (e.g., "1 year", "18 months").
    chart : bool
        Whether to return a chart object.
    template : Literal
        The template/theme to use for the plotly figure.
    """

    country: Literal[
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
    ] = Field(
        default="united_states",
        title="Country for humblCOMPASS data",
        description=HUMBLCOMPASS_QUERY_DESCRIPTIONS.get("country", ""),
    )
    cli_start_date: str | None = Field(
        default=None,
        title="Adjusted start date for CLI data",
        description="The adjusted start date for CLI data collection.",
    )
    cpi_start_date: str | None = Field(
        default=None,
        title="Adjusted start date for CPI data",
        description="The adjusted start date for CPI data collection.",
    )
    z_score: str | None = Field(
        default=None,
        title="Z-score calculation window",
        description="The time window for z-score calculation (e.g., '1 year', '18 months').",
    )
    chart: bool = Field(
        default=False,
        title="Results Chart",
        description=HUMBLCOMPASS_QUERY_DESCRIPTIONS.get("chart", ""),
    )
    template: Literal[
        "humbl_dark",
        "humbl_light",
        "ggplot2",
        "seaborn",
        "simple_white",
        "plotly",
        "plotly_white",
        "plotly_dark",
        "presentation",
        "xgridoff",
        "ygridoff",
        "gridon",
        "none",
    ] = Field(
        default="humbl_dark",
        title="Plotly Template",
        description=HUMBLCOMPASS_QUERY_DESCRIPTIONS.get("template", ""),
    )
    recommendations: bool = Field(
        default=False,
        title="Investment Recommendations",
        description="Whether to include investment recommendations based on the HUMBL regime.",
    )


REGIME_RECOMMENDATIONS: dict[str, RegimeRecommendations] = {
    "humblBOOM": RegimeRecommendations(
        asset_classes=RecommendationCategory(
            best=[
                AssetRecommendation.EQUITIES,
                AssetRecommendation.CREDIT,
                AssetRecommendation.COMMODITIES,
                AssetRecommendation.FX,
            ],
            worst=[AssetRecommendation.FIXED_INCOME, AssetRecommendation.USD],
            rationale="Strong growth and inflation expectations favor risk assets",
        ),
        equity_sectors=RecommendationCategory(
            best=[
                AssetRecommendation.TECHNOLOGY,
                AssetRecommendation.CONSUMER_DISCRETIONARY,
                AssetRecommendation.MATERIALS,
                AssetRecommendation.INDUSTRIALS,
            ],
            worst=[
                AssetRecommendation.UTILITIES,
                AssetRecommendation.REITS,
                AssetRecommendation.CONSUMER_STAPLES,
                AssetRecommendation.FINANCIALS,
            ],
            rationale="Growth sectors outperform in expansionary environments",
        ),
        equity_factors=RecommendationCategory(
            best=[
                AssetRecommendation.HIGH_BETA,
                AssetRecommendation.MOMENTUM,
                AssetRecommendation.CYCLICALS,
                AssetRecommendation.SECULAR_GROWTH,
            ],
            worst=[
                AssetRecommendation.LOW_BETA,
                AssetRecommendation.DEFENSIVES,
                AssetRecommendation.VALUE,
                AssetRecommendation.DIVIDEND_YIELD,
            ],
            rationale="Risk-on factors perform well in growth environments",
        ),
        fixed_income=RecommendationCategory(
            best=[
                AssetRecommendation.BDCS,
                AssetRecommendation.CONVERTIBLES,
                AssetRecommendation.HY_CREDIT,
                AssetRecommendation.EM_DEBT,
            ],
            worst=[
                AssetRecommendation.TIPS,
                AssetRecommendation.SHORT_DURATION_TREASURIES,
                AssetRecommendation.MORTGAGE_BACKED_SECURITIES,
                AssetRecommendation.MEDIUM_DURATION_TREASURIES,
            ],
            rationale="Credit risk outperforms duration risk",
        ),
        regime_description="Accelerating growth and decelerating inflation favors risk assets with big market multiples in equities, junk bonds, and real growth. This is the time to BUY 'anything'!",
        key_risks=[
            "Inflation Resurgence",
            "Policy Tightening",
            "Valuation Expansion",
        ],
    ),
    "humblBUST": RegimeRecommendations(
        asset_classes=RecommendationCategory(
            best=[
                AssetRecommendation.FIXED_INCOME,
                AssetRecommendation.GOLD,
                AssetRecommendation.USD,
            ],
            worst=[
                AssetRecommendation.COMMODITIES,
                AssetRecommendation.EQUITIES,
                AssetRecommendation.CREDIT,
                AssetRecommendation.FX,
            ],
            rationale="Deflationary environment favors safe-haven assets and cash",
        ),
        equity_sectors=RecommendationCategory(
            best=[
                AssetRecommendation.CONSUMER_STAPLES,
                AssetRecommendation.UTILITIES,
                AssetRecommendation.REITS,
                AssetRecommendation.HEALTH_CARE,
            ],
            worst=[
                AssetRecommendation.ENERGY,
                AssetRecommendation.TECHNOLOGY,
                AssetRecommendation.INDUSTRIALS,
                AssetRecommendation.FINANCIALS,
            ],
            rationale="Defensive sectors outperform in contractionary environments",
        ),
        equity_factors=RecommendationCategory(
            best=[
                AssetRecommendation.LOW_BETA,
                AssetRecommendation.DIVIDEND_YIELD,
                AssetRecommendation.QUALITY,
                AssetRecommendation.DEFENSIVES,
            ],
            worst=[
                AssetRecommendation.HIGH_BETA,
                AssetRecommendation.MOMENTUM,
                AssetRecommendation.CYCLICALS,
                AssetRecommendation.SECULAR_GROWTH,
            ],
            rationale="Low-risk factors outperform in risk-off environments",
        ),
        fixed_income=RecommendationCategory(
            best=[
                AssetRecommendation.LONG_DURATION_TREASURIES,
                AssetRecommendation.MEDIUM_DURATION_TREASURIES,
                AssetRecommendation.IG_CREDIT,
                AssetRecommendation.MUNIS,
            ],
            worst=[
                AssetRecommendation.PREFERREDS,
                AssetRecommendation.EM_LOCAL_CURRENCY,
                AssetRecommendation.BDCS,
                AssetRecommendation.LEVERAGED_LOANS,
            ],
            rationale="Duration risk outperforms credit risk in deflationary environments",
        ),
        regime_description="Deflationary environment favors treasuries and cash while avoiding high yield credit and stocks",
        key_risks=[
            "Policy response delay",
            "Deflation spiral",
            "Credit market stress",
        ],
    ),
    "humblBOUNCE": RegimeRecommendations(
        asset_classes=RecommendationCategory(
            best=[
                AssetRecommendation.COMMODITIES,
                AssetRecommendation.EQUITIES,
                AssetRecommendation.CREDIT,
                AssetRecommendation.FX,
            ],
            worst=[
                AssetRecommendation.FIXED_INCOME,
                AssetRecommendation.USD,
            ],
            rationale="Rising yields and improving growth favor risk assets",
        ),
        equity_sectors=RecommendationCategory(
            best=[
                AssetRecommendation.TECHNOLOGY,
                AssetRecommendation.CONSUMER_DISCRETIONARY,
                AssetRecommendation.INDUSTRIALS,
                AssetRecommendation.MATERIALS,
            ],
            worst=[
                AssetRecommendation.TELECOM,
                AssetRecommendation.UTILITIES,
                AssetRecommendation.REITS,
                AssetRecommendation.CONSUMER_STAPLES,
            ],
            rationale="Growth and cyclical sectors benefit from improving conditions",
        ),
        equity_factors=RecommendationCategory(
            best=[
                AssetRecommendation.SECULAR_GROWTH,
                AssetRecommendation.MOMENTUM,
                AssetRecommendation.CYCLICAL_GROWTH,
                AssetRecommendation.SMALL_CAPS,
            ],
            worst=[
                AssetRecommendation.LOW_BETA,
                AssetRecommendation.VALUE,
                AssetRecommendation.DIVIDEND_YIELD,
                AssetRecommendation.DEFENSIVES,
            ],
            rationale="Growth and high-beta factors lead in recovery phases",
        ),
        fixed_income=RecommendationCategory(
            best=[
                AssetRecommendation.CONVERTIBLES,
                AssetRecommendation.BDCS,
                AssetRecommendation.PREFERREDS,
                AssetRecommendation.LEVERAGED_LOANS,
            ],
            worst=[
                AssetRecommendation.LONG_DURATION_TREASURIES,
                AssetRecommendation.MEDIUM_DURATION_TREASURIES,
                AssetRecommendation.MUNIS,
                AssetRecommendation.IG_CREDIT,
            ],
            rationale="Credit-sensitive sectors outperform as rates rise and spreads tighten",
        ),
        regime_description="Recovery phase with rising bond yields, improving financials, and strengthening commodities",
        key_risks=[
            "False recovery",
            "Policy tightening too soon",
            "Inflation resurgence",
        ],
    ),
    "humblBLOAT": RegimeRecommendations(
        asset_classes=RecommendationCategory(
            best=[
                AssetRecommendation.GOLD,
                AssetRecommendation.COMMODITIES,
            ],
            worst=[
                AssetRecommendation.CREDIT,
            ],
            rationale="USD devaluation and money printing favor real assets",
        ),
        equity_sectors=RecommendationCategory(
            best=[
                AssetRecommendation.UTILITIES,
                AssetRecommendation.TECHNOLOGY,
                AssetRecommendation.ENERGY,
                AssetRecommendation.INDUSTRIALS,
            ],
            worst=[
                AssetRecommendation.FINANCIALS,
                AssetRecommendation.REITS,
                AssetRecommendation.MATERIALS,
                AssetRecommendation.TELECOM,
            ],
            rationale="Sectors with pricing power and real asset exposure outperform",
        ),
        equity_factors=RecommendationCategory(
            best=[
                AssetRecommendation.SECULAR_GROWTH,
                AssetRecommendation.MOMENTUM,
                AssetRecommendation.MID_CAPS,
                AssetRecommendation.LOW_BETA,
            ],
            worst=[
                AssetRecommendation.SMALL_CAPS,
                AssetRecommendation.DIVIDEND_YIELD,
                AssetRecommendation.VALUE,
                AssetRecommendation.DEFENSIVES,
            ],
            rationale="Quality growth outperforms as real growth slows but inflation accelerates",
        ),
        fixed_income=RecommendationCategory(
            best=[
                AssetRecommendation.MUNIS,
                AssetRecommendation.EM_DEBT,
                AssetRecommendation.LONG_DURATION_TREASURIES,
                AssetRecommendation.TIPS,
            ],
            worst=[
                AssetRecommendation.BDCS,
                AssetRecommendation.PREFERREDS,
                AssetRecommendation.CONVERTIBLES,
                AssetRecommendation.LEVERAGED_LOANS,
            ],
            rationale="High-quality duration outperforms as real yields decline",
        ),
        regime_description="Central Bank Policy response to economic slowdown creates illusion of growth through inflation acceleration while real growth slows",
        key_risks=[
            "Stagflation",
            "Policy Credibility Loss",
            "Real Growth Deterioration",
        ],
    ),
}


class HumblCompassData(Data):
    """
    Data model for the humbl_compass command, a Pandera.Polars Model.

    This Data model is used to validate data in the `.transform_data()` method of the `HumblCompassFetcher` class.
    """

    date_month_start: pl.Date = pa.Field(
        default=None,
        title="Date",
        description=HUMBLCOMPASS_DATA_DESCRIPTIONS["date"],
    )
    country: pl.Utf8 = pa.Field(
        default=None,
        title="Country",
        description=HUMBLCOMPASS_DATA_DESCRIPTIONS["country"],
    )
    cpi: pl.Float64 = pa.Field(
        default=None,
        title="Consumer Price Index (CPI)",
        description=HUMBLCOMPASS_DATA_DESCRIPTIONS["cpi"],
    )
    cpi_3m_delta: pl.Float64 = pa.Field(
        default=None,
        title="Consumer Price Index (CPI) 3-Month Delta",
        description=HUMBLCOMPASS_DATA_DESCRIPTIONS["cpi_3m_delta"],
    )
    cpi_zscore: pl.Float64 | None = pa.Field(
        default=None,
        title="Consumer Price Index (CPI) 1-Year Z-Score",
        description=HUMBLCOMPASS_DATA_DESCRIPTIONS["cpi_1yr_zscore"],
        nullable=True,
    )
    cli: pl.Float64 = pa.Field(
        default=None,
        title="Composite Leading Indicator (CLI)",
        description=HUMBLCOMPASS_DATA_DESCRIPTIONS["cli"],
    )
    cli_3m_delta: pl.Float64 = pa.Field(
        default=None,
        title="Composite Leading Indicator (CLI) 3-Month Delta",
        description=HUMBLCOMPASS_DATA_DESCRIPTIONS["cli_3m_delta"],
    )
    cli_zscore: pl.Float64 | None = pa.Field(
        default=None,
        title="Composite Leading Indicator (CLI) 1-Year Z-Score",
        description=HUMBLCOMPASS_DATA_DESCRIPTIONS["cli_1yr_zscore"],
        nullable=True,
    )
    humbl_regime: pl.Utf8 = pa.Field(
        default=None,
        title="HUMBL Regime",
        description=HUMBLCOMPASS_DATA_DESCRIPTIONS["humbl_regime"],
    )


class HumblCompassFetcher:
    """
    Fetcher for the HumblCompass command.

    Parameters
    ----------
    context_params : ToolboxQueryParams
        The context parameters for the Toolbox query.
    command_params : HumblCompassQueryParams
        The command-specific parameters for the HumblCompass query.

    Attributes
    ----------
    context_params : ToolboxQueryParams
        Stores the context parameters passed during initialization.
    command_params : HumblCompassQueryParams
        Stores the command-specific parameters passed during initialization.
    data : pl.DataFrame
        The raw data extracted from the data provider, before transformation.

    Methods
    -------
    transform_query()
        Transform the command-specific parameters into a query.
    extract_data()
        Extracts the data from the provider and returns it as a Polars DataFrame.
    transform_data()
        Transforms the command-specific data according to the HumblCompass logic.
    fetch_data()
        Execute TET Pattern.
    backtest(**kwargs)
        Execute backtest calculations on the compass data using additional parameters.

    Returns
    -------
    HumblObject
        results : HumblCompassData
            Serializable results.
        provider : Literal['fmp', 'intrinio', 'polygon', 'tiingo', 'yfinance']
            Provider name.
        warnings : Optional[List[Warning_]]
            List of warnings.
        chart : Optional[Chart]
            Chart object.
        context_params : ToolboxQueryParams
            Context-specific parameters.
        command_params : HumblCompassQueryParams
            Command-specific parameters.
    """

    def __init__(
        self,
        context_params: ToolboxQueryParams,
        command_params: HumblCompassQueryParams,
    ):
        """
        Initialize the HumblCompassFetcher with context and command parameters.

        Parameters
        ----------
        context_params : ToolboxQueryParams
            The context parameters for the Toolbox query.
        command_params : HumblCompassQueryParams
            The command-specific parameters for the HumblCompass query.
        """
        self.context_params = context_params
        self.command_params = command_params
        self.warnings = []  # Initialize warnings list

    def transform_query(self):
        """
        Transform the command-specific parameters into a query.

        If command_params is not provided, it initializes a default HumblCompassQueryParams object.
        Calculates adjusted start dates for CLI and CPI data collection.
        """
        if not self.command_params:
            self.command_params = HumblCompassQueryParams()
        elif isinstance(self.command_params, dict):
            self.command_params = HumblCompassQueryParams(**self.command_params)

        # Calculate adjusted start dates
        if isinstance(self.context_params.start_date, str):
            start_date = pl.Series(
                [datetime.strptime(self.context_params.start_date, "%Y-%m-%d")]
            )
        else:
            start_date = pl.Series([self.context_params.start_date])

        # Calculate z-score window in months
        self.z_score_months = 0
        if (
            self.command_params.z_score is not None
            and self.context_params.membership != "humblPEON"
        ):
            z_score_months_str = _window_format(
                self.command_params.z_score, _return_timedelta=False
            )
            self.z_score_months = _window_format_monthly(z_score_months_str)
        if 0 < self.z_score_months < 3:
            logger.warning(
                "Z-score calculation requires a minimum of 3 months. Setting z_score to 3 months."
            )
            self.z_score_months = 3
        elif self.context_params.membership == "humblPEON":
            logger.warning(
                "Z-score is not calculated for humblPEON membership level."
            )

        cli_start_date = start_date.dt.offset_by(
            f"-{4 + self.z_score_months}mo"
        ).dt.strftime("%Y-%m-%d")[0]
        cpi_start_date = start_date.dt.offset_by(
            f"-{4 + self.z_score_months}mo"
        ).dt.strftime("%Y-%m-%d")[0]

        # Update the command_params with the new start dates
        self.command_params = self.command_params.model_copy(
            update={
                "cli_start_date": cli_start_date,
                "cpi_start_date": cpi_start_date,
            }
        )
        msg = (
            f"CLI start date: {self.command_params.cli_start_date} and CPI start date: {self.command_params.cpi_start_date}. "
            f"Dates are adjusted to account for CLI data release lag and z-score calculation window."
        )
        logger.info(msg)

    @collect_warnings
    async def extract_data(self):
        """
        Extract the data from the provider and returns it as a Polars DataFrame.

        Returns
        -------
        self
            The HumblCompassFetcher instance with extracted data.
        """
        # Collect CLI Data via API client
        cli_query_params = EconomyCompositeLeadingIndicatorQueryParams(
            start_date=self.command_params.cli_start_date,
            end_date=self.context_params.end_date,
            provider="oecd",
            country=self.command_params.country,
        )
        api_client = OpenBBAPIClient()
        cli_response = await api_client.fetch_data(
            obb_path="economy.composite_leading_indicator",
            api_query_params=cli_query_params,
        )
        self.oecd_cli_data = cli_response.to_polars(collect=False)
        self.oecd_cli_data = self.oecd_cli_data.rename(
            {"value": "cli"}
        ).with_columns(
            [pl.col("date").dt.month_start().alias("date_month_start")]
        )

        # Collect YoY CPI Data via API client
        cpi_query_params = EconomyConsumerPriceIndexQueryParams(
            start_date=self.command_params.cpi_start_date,
            end_date=self.context_params.end_date,
            frequency="monthly",
            country=self.command_params.country,
            transform="yoy",
            provider="oecd",
            harmonized=False,
            expenditure="total",
        )
        cpi_response = await api_client.fetch_data(
            obb_path="economy.cpi",
            api_query_params=cpi_query_params,
        )
        self.oecd_cpi_data = cpi_response.to_polars(collect=False)
        self.oecd_cpi_data = self.oecd_cpi_data.rename(
            {"value": "cpi"}
        ).with_columns(
            [pl.col("date").dt.month_start().alias("date_month_start")]
        )
        return self

    @collect_warnings
    def transform_data(self):
        """
        Transform the command-specific data according to the humbl_compass logic.

        Returns
        -------
        self
            The HumblCompassFetcher instance with transformed data.
        """
        # Combine CLI and CPI data
        # CLI data is released before CPI data, so we use a left join
        combined_data = (
            self.oecd_cli_data.join(
                self.oecd_cpi_data.with_columns(
                    [
                        pl.col("country")
                        .str.replace("_", " ")
                        .str.to_titlecase(),
                        pl.col("date_month_start").cast(pl.Date),
                    ]
                ),
                on=["date_month_start", "country"],
                how="inner",  # Changed to inner from left to only return rows where dates & country match
                suffix="_cpi",
            )
            .sort("date_month_start")
            .with_columns(
                [
                    pl.col("country").cast(pl.Utf8),
                    pl.col("cli").cast(pl.Float64),
                    pl.col("cpi").cast(pl.Float64) * 100,
                ]
            )
            .rename({"date": "date_cli"})
            .select(
                [
                    "date_month_start",
                    "date_cli",
                    "date_cpi",
                    "country",
                    "cli",
                    "cpi",
                ]
            )
        )

        # Calculate 3-month deltas with adaptive shift based on data frequency
        transformed_data = combined_data.with_columns(
            [
                # Calculate the average time difference between observations in days
                (
                    pl.col("date_month_start")
                    .diff()
                    .dt.total_days()  # Get total days directly
                    .mean()
                    .over("country")
                    .alias("avg_days_between_obs")
                )
            ]
        )

        # Now use this to determine the appropriate shift
        transformed_data = transformed_data.with_columns(
            [
                pl.when(pl.col("avg_days_between_obs") >= 85)  # ~3 months
                .then(
                    pl.col("cli") - pl.col("cli").shift(1)
                )  # For quarterly data
                .otherwise(
                    pl.col("cli") - pl.col("cli").shift(3)
                )  # For monthly data
                .alias("cli_3m_delta"),
                pl.when(pl.col("avg_days_between_obs") >= 85)  # ~3 months
                .then(
                    pl.col("cpi") - pl.col("cpi").shift(1)
                )  # For quarterly data
                .otherwise(
                    pl.col("cpi") - pl.col("cpi").shift(3)
                )  # For monthly data
                .alias("cpi_3m_delta"),
            ]
        ).drop("avg_days_between_obs")

        # Add this after calculating 3-month deltas in transform_data()
        transformed_data = transformed_data.with_columns(
            [
                pl.when(
                    (pl.col("cpi_3m_delta") > 0) & (pl.col("cli_3m_delta") < 0)
                )
                .then(pl.lit("humblBLOAT"))
                .when(
                    (pl.col("cpi_3m_delta") > 0) & (pl.col("cli_3m_delta") > 0)
                )
                .then(pl.lit("humblBOUNCE"))
                .when(
                    (pl.col("cpi_3m_delta") < 0) & (pl.col("cli_3m_delta") > 0)
                )
                .then(pl.lit("humblBOOM"))
                .when(
                    (pl.col("cpi_3m_delta") < 0) & (pl.col("cli_3m_delta") < 0)
                )
                .then(pl.lit("humblBUST"))
                .otherwise(None)
                .alias("humbl_regime")
            ]
        )

        # Calculate z-scores only if self.z_score_months is greater than 0 and membership is not humblPEON
        if (
            self.z_score_months >= 3
            and self.context_params.membership != "humblPEON"
        ):
            transformed_data = transformed_data.with_columns(
                [
                    pl.when(
                        pl.col("cli").count().over("country")
                        >= self.z_score_months
                    )
                    .then(
                        (
                            pl.col("cli")
                            - pl.col("cli").rolling_mean(self.z_score_months)
                        )
                        / pl.col("cli").rolling_std(self.z_score_months)
                    )
                    .alias("cli_zscore"),
                    pl.when(
                        pl.col("cpi").count().over("country")
                        >= self.z_score_months
                    )
                    .then(
                        (
                            pl.col("cpi")
                            - pl.col("cpi").rolling_mean(self.z_score_months)
                        )
                        / pl.col("cpi").rolling_std(self.z_score_months)
                    )
                    .alias("cpi_zscore"),
                ]
            )

        # Select columns based on whether z-scores were calculated
        columns_to_select = [
            pl.col("date_month_start"),
            pl.col("country"),
            pl.col("cpi").round(2),
            pl.col("cpi_3m_delta").round(2),
            pl.col("cli").round(2),
            pl.col("cli_3m_delta").round(2),
            pl.col("humbl_regime"),
        ]

        if (
            self.z_score_months >= 3
            and self.context_params.membership != "humblPEON"
        ):
            columns_to_select.extend(
                [
                    pl.col("cpi_zscore").round(2),
                    pl.col("cli_zscore").round(2),
                ]
            )

        transformed_data = transformed_data.select(columns_to_select)

        # Validate the data using HumblCompassData and collect result BEFORE serialization.
        raw_data = (
            transformed_data.collect().drop_nulls()
        )  # <-- keep raw data for backtest
        self._raw_transformed_df = raw_data  # store raw transformed data

        self.transformed_data = HumblCompassData(raw_data).lazy()

        # Generate chart if requested
        self.chart = None
        if self.command_params.chart:
            self.chart = generate_plots(
                self.transformed_data,
                template=ChartTemplate(self.command_params.template),
            )

        # Add warning if z_score is None
        if self.command_params.z_score is None:
            warnings.warn(
                "Z-score defaulted to None. No z-score data will be calculated.",
                category=HumblDataWarning,
                stacklevel=1,
            )

        # Add recommendations if requested
        if self.command_params.recommendations:
            latest_regime = (
                self.transformed_data.select(pl.col("humbl_regime"))
                .collect()
                .row(-1)[0]
            )

            if latest_regime not in REGIME_RECOMMENDATIONS:
                warnings.warn(
                    f"No recommendations available for regime: {latest_regime}",
                    category=HumblDataWarning,
                    stacklevel=1,
                )
            else:
                recommendations = REGIME_RECOMMENDATIONS[latest_regime]
                if not hasattr(self, "extra"):
                    self.extra = {}
                self.extra["humbl_regime_recommendations"] = (
                    recommendations.model_dump()
                )

        # Finally, serialize final transformed data.
        self.transformed_data = serialize_lazyframe_to_ipc(
            self.transformed_data
        )
        return self

    @log_start_end(logger=logger)
    @cached(
        ttl=getattr(env, "REDIS_CACHE_TTL", 86400),
        key_builder=humbl_compass_key_builder,
        serializer=CustomPickleSerializer(),
        cache=RedisCache,
        **get_redis_cache_config(namespace="humbl_compass"),
        plugins=[LogCacheHitPlugin(name="humbl_compass")],
    )
    async def fetch_data(self):
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
        await self.extract_data()
        logger.debug("Running .transform_data()")
        self.transform_data()

        # Initialize warnings list if it doesn't exist
        if not hasattr(self.context_params, "warnings"):
            self.context_params.warnings = []

        # Combine warnings from both sources
        all_warnings = self.context_params.warnings + self.warnings

        # Create HumblObject with raw data in extra for backtest
        result = HumblObject(
            results=self.transformed_data,
            provider=self.context_params.provider,
            warnings=all_warnings,
            chart=self.chart,
            context_params=self.context_params,
            command_params=self.command_params,
            extra=self.extra if hasattr(self, "extra") else {},
        )
        return result
