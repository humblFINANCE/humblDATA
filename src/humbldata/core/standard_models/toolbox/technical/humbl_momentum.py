"""
Momentum Standard Model.

Context: Toolbox || Category: Technical || Command: momentum.

This module is used to define the QueryParams and Data model for the
Momentum command.
"""

from typing import Literal, TypeVar

import pandera.polars as pa
import polars as pl
from pydantic import Field, field_validator

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.utils.core_helpers import serialize_lazyframe_to_ipc
from humbldata.core.utils.env import Env
from humbldata.core.utils.logger import log_start_end, setup_logger
from humbldata.toolbox.technical.humbl_momentum.view import generate_plots
from humbldata.core.utils.openbb_api_client import OpenBBAPIClient
from humbldata.core.standard_models.openbbapi.EquityPriceHistoricalQueryParams import (
    EquityPriceHistoricalQueryParams,
)

env = Env()
Q = TypeVar("Q", bound=ToolboxQueryParams)
logger = setup_logger("HumblMomentumFetcher", level=env.LOGGER_LEVEL)

MOMENTUM_QUERY_DESCRIPTIONS = {
    "method": "Method to calculate momentum (log, simple, or shift)",
    "window": "Window to calculate momentum over",
    "chart": "Whether to generate a chart",
    "template": "Plotly template to use for the chart",
}


class HumblMomentumQueryParams(QueryParams):
    """
    QueryParams model for the Momentum command.

    Parameters
    ----------
    method : Literal["log", "simple", "shift"]
        Method to calculate momentum
    window : str
        Window to calculate momentum over
    """

    method: Literal["log", "simple", "shift"] = Field(
        default="log",
        title="Calculation Method",
        description=MOMENTUM_QUERY_DESCRIPTIONS["method"],
    )
    window: str = Field(
        default="1d",
        title="Window",
        description=MOMENTUM_QUERY_DESCRIPTIONS["window"],
    )
    chart: bool = Field(
        default=False,
        title="Results Chart",
        description=MOMENTUM_QUERY_DESCRIPTIONS["chart"],
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
        description=MOMENTUM_QUERY_DESCRIPTIONS.get("template", ""),
    )

    @field_validator("method")
    @classmethod
    def validate_method(
        cls, v: Literal["log", "simple", "shift"]
    ) -> Literal["log", "simple", "shift"]:
        return v


class MomentumData(Data):
    """
    Data model for the momentum command, a Pandera.Polars Model.

    This Data model is used to validate data in the `.transform_data()` method of the `MomentumFetcher` class.
    """

    date: pl.Date = pa.Field(
        default=None,
        title="Date",
        description="The date of the data point.",
    )
    symbol: str = pa.Field(
        default=None,
        title="Symbol",
        description="The stock symbol.",
    )
    close: float | None = pa.Field(
        default=None,
        nullable=True,
        title="Close",
        description="The close price of the stock.",
    )
    shifted: float | None = pa.Field(
        default=None,
        nullable=True,
        title="Shifted",
        description="The shifted value.",
    )
    momentum: float | None = pa.Field(
        default=None,
        nullable=True,
        title="Momentum",
        description="The momentum value.",
    )
    momentum_signal: pl.Int8 | None = pa.Field(
        in_range={"min_value": 0, "max_value": 1},
        default=None,
        nullable=True,
        title="Momentum Signal",
        description="The momentum signal value.",
    )

    class Config:  # noqa: D106
        strict = "filter"


class HumblMomentumFetcher:
    """
    Fetcher for the Momentum command.

    Parameters
    ----------
    context_params : ToolboxQueryParams
        The context parameters for the Toolbox query.
    command_params : HumblMomentumQueryParams
        The command-specific parameters for the Momentum query.

    Attributes
    ----------
    context_params : ToolboxQueryParams
        Stores the context parameters passed during initialization.
    command_params : HumblMomentumQueryParams
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
        Transforms the command-specific data according to the Momentum logic.
    fetch_data()
        Execute TET Pattern.

    Returns
    -------
    HumblObject
        results : MomentumData
            Serializable results.
        provider : Literal['fmp', 'intrinio', 'polygon', 'tiingo', 'yfinance']
            Provider name.
        warnings : List[Warning_]
            List of warnings from both context and command.
        chart : Optional[Chart]
            Chart object.
        context_params : ToolboxQueryParams
            Context-specific parameters.
        command_params : HumblMomentumQueryParams
            Command-specific parameters.
        extra : dict
            Additional metadata or results.
    """

    def __init__(
        self,
        context_params: ToolboxQueryParams,
        command_params: HumblMomentumQueryParams,
    ):
        """
        Initialize the HumblMomentumFetcher with context and command parameters.

        Parameters
        ----------
        context_params : ToolboxQueryParams
            The context parameters for the Toolbox query.
        command_params : HumblMomentumQueryParams
            The command-specific parameters for the Momentum query.
        """
        self.context_params = context_params
        self.command_params = command_params
        self.warnings = []
        self.extra = {}
        self.chart = None

    def transform_query(self):
        """
        Transform the command-specific parameters into a query.

        If command_params is not provided, it initializes a default HumblMomentumQueryParams object.
        """
        if not self.command_params:
            self.command_params = HumblMomentumQueryParams()
        else:
            self.command_params = HumblMomentumQueryParams(
                **self.command_params
            )

    async def extract_data(self):
        """
        Extract the data from the provider and returns it as a Polars DataFrame.

        Returns
        -------
        pl.DataFrame
            The extracted data as a Polars DataFrame.
        """
        api_query_params = EquityPriceHistoricalQueryParams(
            symbol=self.context_params.symbols,
            start_date=self.context_params.start_date,
            end_date=self.context_params.end_date,
            provider=self.context_params.provider,
        )
        api_client = OpenBBAPIClient()
        api_response = await api_client.fetch_data(
            obb_path="equity.price.historical",
            api_query_params=api_query_params,
        )
        self.equity_historical_data = api_response.to_polars(collect=False)

        if len(self.context_params.symbols) == 1:
            self.equity_historical_data = (
                self.equity_historical_data.with_columns(
                    symbol=pl.lit(self.context_params.symbols[0])
                )
            )
        return self

    def transform_data(self):
        """
        Transform the command-specific data according to the momentum logic.

        Returns
        -------
        pl.DataFrame
            The transformed data as a Polars DataFrame
        """
        try:
            logger.debug("Transforming data with momentum calculation")

            # Import momentum calculation
            from humbldata.toolbox.technical.humbl_momentum.model import (
                calc_humbl_momentum,
            )

            # Calculate momentum using the extracted data
            self.transformed_data = calc_humbl_momentum(
                data=self.equity_historical_data,
                method=self.command_params.method,
                window=self.command_params.window,
            )

            # Validate the transformed data
            self.transformed_data = MomentumData(
                self.transformed_data.collect().drop_nulls()
            ).lazy()

            if self.command_params.chart:
                self.chart = generate_plots(
                    self.transformed_data,
                    self.equity_historical_data,
                    method=self.command_params.method,
                    template=self.command_params.template,
                )
            else:
                self.chart = None

        except Exception as e:
            msg = f"Momentum transformation failed: {e!s}"
            logger.exception(msg)
            raise HumblDataError(msg) from e

        self.transformed_data = serialize_lazyframe_to_ipc(
            self.transformed_data
        )
        return self

    @log_start_end(logger=logger)
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
            warnings=all_warnings,  # Use combined warnings
            chart=self.chart,
            context_params=self.context_params,
            command_params=self.command_params,
            extra=self.extra,  # pipe in extra from transform_data()
        )
