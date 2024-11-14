"""
HumblCompass Standard Model.

Context: Toolbox || Category: Fundamental || Command: humbl_compass.

This module is used to define the QueryParams and Data model for the
HumblCompass command.
"""

from datetime import datetime
from typing import Literal, Optional, TypeVar

import pandera.polars as pa
import polars as pl
from openbb import obb
from pydantic import Field

from humbldata.core.standard_models.abstract.chart import ChartTemplate
from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.utils.env import Env
from humbldata.core.utils.logger import log_start_end, setup_logger
from humbldata.toolbox.fundamental.humbl_compass.view import generate_plots
from humbldata.toolbox.toolbox_helpers import (
    _window_format,
    _window_format_monthly,
)

env = Env()
Q = TypeVar("Q", bound=ToolboxQueryParams)
logger = setup_logger("HumblCompassFetcher", level=env.LOGGER_LEVEL)

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
    cli_start_date: str = Field(
        default=None,
        title="Adjusted start date for CLI data",
        description="The adjusted start date for CLI data collection.",
    )
    cpi_start_date: str = Field(
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
        elif self.context_params.membership == "humblPEON":
            logger.warning(
                "Z-score is not calculated for humblPEON membership level."
            )

        cli_start_date = start_date.dt.offset_by(
            f"-{4 + self.z_score_months}mo"
        ).dt.strftime("%Y-%m-%d")[0]
        cpi_start_date = start_date.dt.offset_by(
            f"-{3 + self.z_score_months}mo"
        ).dt.strftime("%Y-%m-%d")[0]

        # Update the command_params with the new start dates
        self.command_params = self.command_params.model_copy(
            update={
                "cli_start_date": cli_start_date,
                "cpi_start_date": cpi_start_date,
            }
        )

        logger.info(
            f"CLI start date: {self.command_params.cli_start_date} and CPI start date: {self.command_params.cpi_start_date}. "
            f"Dates are adjusted to account for CLI data release lag and z-score calculation window."
        )

    def extract_data(self):
        """
        Extract the data from the provider and returns it as a Polars DataFrame.

        Returns
        -------
        self
            The HumblCompassFetcher instance with extracted data.
        """
        # Collect CLI Data
        self.oecd_cli_data = (
            obb.economy.composite_leading_indicator(
                start_date=self.command_params.cli_start_date,
                end_date=self.context_params.end_date,
                provider="oecd",
                country=self.command_params.country,
            )
            .to_polars()
            .lazy()
            .rename({"value": "cli"})
            .with_columns(
                [pl.col("date").dt.month_start().alias("date_month_start")]
            )
        )

        # Collect YoY CPI Data
        self.oecd_cpi_data = (
            obb.economy.cpi(
                start_date=self.command_params.cpi_start_date,
                end_date=self.context_params.end_date,
                frequency="monthly",
                country=self.command_params.country,
                transform="yoy",
                provider="oecd",
                harmonized=False,
                expenditure="total",
            )
            .to_polars()
            .lazy()
            .rename({"value": "cpi"})
            .with_columns(
                [pl.col("date").dt.month_start().alias("date_month_start")]
            )
        )
        return self

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
                self.oecd_cpi_data,
                on=["date_month_start", "country"],
                how="left",
                suffix="_cpi",
            )
            .sort("date_month_start")
            .with_columns(
                [
                    pl.col("country").cast(pl.Utf8),
                    pl.col("cli").cast(pl.Float64),
                    pl.col("cpi").cast(pl.Float64)
                    * 100,  # Convert CPI to percentage
                ]
            )
            .rename(
                {
                    "date": "date_cli",
                }
            )
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

        # Calculate 3-month deltas
        delta_window = 3
        transformed_data = combined_data.with_columns(
            [
                (pl.col("cli") - pl.col("cli").shift(delta_window)).alias(
                    "cli_3m_delta"
                ),
                (pl.col("cpi") - pl.col("cpi").shift(delta_window)).alias(
                    "cpi_3m_delta"
                ),
            ]
        )

        # Calculate z-scores only if self.z_score_months is greater than 0 and membership is not humblPEON
        if (
            self.z_score_months > 0
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
        ]

        if (
            self.z_score_months > 0
            and self.context_params.membership != "humblPEON"
        ):
            columns_to_select.extend(
                [
                    pl.col("cpi_zscore").round(2),
                    pl.col("cli_zscore").round(2),
                ]
            )

        self.transformed_data = transformed_data.select(columns_to_select)

        # Validate the data using HumblCompassData
        self.transformed_data = HumblCompassData(
            self.transformed_data.collect().drop_nulls()  # removes preceding 3 months used for delta calculations
        ).lazy()

        # Generate chart if requested
        self.chart = None
        if self.command_params.chart:
            self.chart = generate_plots(
                self.transformed_data,
                template=ChartTemplate(self.command_params.template),
            )

        self.transformed_data = self.transformed_data.serialize(format="binary")

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
        self.transform_query()
        self.extract_data()
        self.transform_data()

        if not hasattr(self.context_params, "warnings"):
            self.context_params.warnings = []

        return HumblObject(
            results=self.transformed_data,
            provider=self.context_params.provider,
            warnings=self.context_params.warnings,
            chart=self.chart,
            context_params=self.context_params,
            command_params=self.command_params,
        )
