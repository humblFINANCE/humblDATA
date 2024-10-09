"""
HumblCompass Standard Model.

Context: Toolbox || Category: Fundamental || Command: humbl_compass.

This module is used to define the QueryParams and Data model for the
HumblCompass command.
"""

from typing import Literal, TypeVar

import pandera.polars as pa
import polars as pl
from openbb import obb
from pydantic import Field, field_validator

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.utils.env import Env
from humbldata.core.utils.logger import log_start_end, setup_logger

env = Env()
Q = TypeVar("Q", bound=ToolboxQueryParams)
logger = setup_logger("HumblCompassFetcher", level=env.LOGGER_LEVEL)

HUMBLCOMPASS_QUERY_DESCRIPTIONS = {
    "example_field1": "Description for example field 1",
    "example_field2": "Description for example field 2",
}

HUMBLCOMPASS_DATA_DESCRIPTIONS = {
    "date": "The date of the data point",
    "country": "The country or group of countries the data represents",
    "cpi": "Consumer Price Index (CPI) value",
    "cpi_3m_delta": "3-month delta of CPI",
    "cpi_3yr_zscore": "3-year trailing z-score of CPI",
    "cli": "Composite Leading Indicator (CLI) value",
    "cli_3m_delta": "3-month delta of CLI",
    "cli_3yr_zscore": "3-year trailing z-score of CLI",
    "humbl_regime": "HUMBL Regime classification based on CPI and CLI values",
}


class HumblCompassQueryParams(QueryParams):
    """
    QueryParams model for the HumblCompass command, a Pydantic v2 model.

    Parameters
    ----------
    country : Literal
        The country or group of countries to collect humblCOMPASS data for.
        Default is "united_states".
        Possible values include:
        - Individual countries: "australia", "brazil", "canada", "china", "france",
        "germany", "india", "indonesia", "italy", "japan", "mexico", "south_africa",
        "south_korea", "spain", "turkey", "united_kingdom", "united_states"
        - Country groups: "g20", "g7", "asia5", "north_america", "europe4"
        - "all" for all available countries
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

    # @field_validator("example_field1")
    # @classmethod
    # def validate_example_field1(cls, v: str) -> str:
    #     return v.upper()


class HumblCompassData(Data):
    """
    Data model for the humbl_compass command, a Pandera.Polars Model.

    This Data model is used to validate data in the `.transform_data()` method of the `HumblCompassFetcher` class.
    """

    date: pl.Date = pa.Field(
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
    cpi_3yr_zscore: pl.Float64 = pa.Field(
        default=None,
        title="Consumer Price Index (CPI) 3-Year Z-Score",
        description=HUMBLCOMPASS_DATA_DESCRIPTIONS["cpi_3yr_zscore"],
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
    cli_3yr_zscore: pl.Float64 = pa.Field(
        default=None,
        title="Composite Leading Indicator (CLI) 3-Year Z-Score",
        description=HUMBLCOMPASS_DATA_DESCRIPTIONS["cli_3yr_zscore"],
    )
    humbl_regime: pl.Utf8 = pa.Field(
        default=None,
        title="humblREGIME",
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
        """
        if not self.command_params:
            self.command_params = HumblCompassQueryParams()
        else:
            self.command_params = HumblCompassQueryParams(**self.command_params)

    def extract_data(self):
        """
        Extract the data from the provider and returns it as a Polars DataFrame.

        Returns
        -------
        pl.DataFrame
            The extracted data as a Polars DataFrame.
        """
        # Collect CLI Data
        self.oecd_cli_data = obb.economy.composite_leading_indicator(
            start_date=self.context_params.start_date,
            end_data=self.context_params.end_date,
            provider="oecd",
            country=self.command_params.country,
        )
        # Collect YoY CPI Data
        self.oecd_cpi_data = obb.economy.cpi(
            start_date=self.context_params.start_date,
            end_date=self.context_params.end_date,
            frequency="monthly",
            country=self.command_params.country,
            transform="yoy",
            provider="oecd",
            harmonized=False,
            expenditure="total",
        )
        return self

    def transform_data(self):
        """
        Transform the command-specific data according to the humbl_compass logic.

        Returns
        -------
        pl.DataFrame
            The transformed data as a Polars DataFrame
        """
        # Implement data transformation logic here

        # Implement 3 month delta CLI calc + 3mo delta + 3yr trailing z-score

        # Implement 3 month delta CPI calc + 3mo delta + 3yr trailing z-score

        # Add humblREGIME column based on the CPI and CLI values

        self.transformed_data = HumblCompassData(self.data)
        self.transformed_data = self.transformed_data.serialize()
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
            chart=None,
            context_params=self.context_params,
            command_params=self.command_params,
        )
