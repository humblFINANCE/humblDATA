"""
Mandelbrot Channel Standard Model.

Context: Toolbox || Category: Technical || Command: Mandelbrot Channel.

This module is used to define the QueryParams and Data model for the
Mandelbrot Channel command.
"""

import warnings
from typing import Literal, TypeVar

import pandera.polars as pa
import polars as pl
from pydantic import Field, field_validator

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.abstract.warnings import (
    HumblDataWarning,
    Warning_,
    collect_warnings,
)
from humbldata.core.standard_models.openbbapi.EquityPriceHistoricalQueryParams import (
    EquityPriceHistoricalQueryParams,
)
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.utils.core_helpers import serialize_lazyframe_to_ipc
from humbldata.core.utils.env import Env
from humbldata.core.utils.logger import log_start_end, setup_logger
from humbldata.core.utils.openbb_api_client import OpenBBAPIClient
from humbldata.toolbox.technical.humbl_channel.model import (
    calc_humbl_channel,
    calc_humbl_channel_historical_concurrent,
)
from humbldata.toolbox.technical.humbl_channel.view import generate_plots
from humbldata.toolbox.toolbox_helpers import _window_format

env = Env()
Q = TypeVar("Q", bound=ToolboxQueryParams)
logger = setup_logger("HumblChannelFetcher", level=env.LOGGER_LEVEL)

MANDELBROT_QUERY_DESCRIPTIONS = {
    "window": "The width of the window used for splitting the data into sections for detrending.",
    "rv_adjustment": "Whether to adjust the calculation for realized volatility. If True, the data is filtered to only include observations in the same volatility bucket that the stock is currently in.",
    "rv_method": "The method to calculate the realized volatility. Only need to define when rv_adjustment is True.",
    "rs_method": "The method to use for Range/STD calculation. THis is either, min, max or mean of all RS ranges per window. If not defined, just used the most recent RS window",
    "rv_grouped_mean": "Whether to calculate the the mean value of realized volatility over multiple window lengths",
    "yesterday_close": "If True, use yesterday's close price (second to last row). If False, use today's close price (last row).",
    "historical": "Whether to calculate the Historical Mandelbrot Channel (over-time), and return a time-series of channels from the start to the end date. If False, the Mandelbrot Channel calculation is done aggregating all of the data into one observation. If True, then it will enable daily observations over-time.",
    "chart": "Whether to return a chart object.",
    "template": "The template/theme to use for the plotly figure.",
}


class HumblChannelQueryParams(QueryParams):
    """
    QueryParams model for the Humbl Channel command, a Pydantic v2 model.

    Parameters
    ----------
    window : str
        The width of the window used for splitting the data into sections for
        detrending. Defaults to "1m".
    rv_adjustment : bool
        Whether to adjust the calculation for realized volatility. If True, the
        data is filtered
        to only include observations in the same volatility bucket that the
        stock is currently in. Defaults to True.
    rv_method : str
        The method to calculate the realized volatility. Only need to define
        when rv_adjustment is True. Defaults to "std".
    rs_method : Literal["RS", "RS_min", "RS_max", "RS_mean"]
        The method to use for Range/STD calculation. This is either, min, max
        or mean of all RS ranges
        per window. If not defined, just used the most recent RS window.
        Defaults to "RS".
    rv_grouped_mean : bool
        Whether to calculate the mean value of realized volatility over
        multiple window lengths. Defaults to False.
    yesterday_close : bool
        If True, use yesterday's close price (second to last row). If False, use today's close price (last row).
    momentum : Literal["shift", "log", "simple"] | None
        Method to calculate momentum: 'shift' for simple shift, 'log' for logarithmic ROC, 'simple' for simple ROC. If None, momentum calculation is skipped.
    historical : bool
        Whether to calculate the Historical Mandelbrot Channel (over-time), and
        return a time-series of channels from the start to the end date. If
        False, the Mandelbrot Channel calculation is done aggregating all of the
        data into one observation. If True, then it will enable daily
        observations over-time. Defaults to False.
    chart : bool
        Whether to return a chart object. Defaults to False.
    """

    window: str = Field(
        default="1mo",
        title="Window",
        description=MANDELBROT_QUERY_DESCRIPTIONS.get("window", ""),
    )
    rv_adjustment: bool = Field(
        default=True,
        title="Realized Volatility Adjustment",
        description=MANDELBROT_QUERY_DESCRIPTIONS.get("rv_adjustment", ""),
    )
    rv_method: Literal[
        "std",
        "parkinson",
        "garman_klass",
        "gk",
        "hodges_tompkins",
        "ht",
        "rogers_satchell",
        "rs",
        "yang_zhang",
        "yz",
        "squared_returns",
        "sq",
    ] = Field(
        default="std",
        title="Realized Volatility Method",
        description=MANDELBROT_QUERY_DESCRIPTIONS.get("rv_method", ""),
    )
    rs_method: Literal["RS", "RS_min", "RS_max", "RS_mean"] = Field(
        default="RS",
        title="R/S Method",
        description=MANDELBROT_QUERY_DESCRIPTIONS.get("rs_method", ""),
    )
    rv_grouped_mean: bool = Field(
        default=False,
        title="Realized Volatility Grouped Mean",
        description=MANDELBROT_QUERY_DESCRIPTIONS.get("rv_grouped_mean", ""),
    )
    yesterday_close: bool = Field(
        default=False,
        title="Use Yesterday's Close",
        description="If True, use yesterday's close price (second to last row). If False, use today's close price (last row).",
    )
    momentum: Literal["shift", "log", "simple"] | None = Field(
        default="shift",
        title="Momentum Method",
        description="Method to calculate momentum: 'shift' for simple shift, 'log' for logarithmic ROC, 'simple' for simple ROC. If None, momentum calculation is skipped.",
    )
    historical: bool = Field(
        default=False,
        title="Historical Mandelbrot Channel",
        description=MANDELBROT_QUERY_DESCRIPTIONS.get("historical", ""),
    )
    chart: bool = Field(
        default=False,
        title="Results Chart",
        description=MANDELBROT_QUERY_DESCRIPTIONS.get("chart", ""),
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
        description=MANDELBROT_QUERY_DESCRIPTIONS.get("template", ""),
    )

    @field_validator("window", mode="after", check_fields=False)
    @classmethod
    def window_format(cls, v) -> str:
        """
        Format the window string into a standardized format.

        Parameters
        ----------
        v : str
            The window size as a string.

        Returns
        -------
        str
            The window string in a standardized format.

        Raises
        ------
        ValueError
            If the input is not a string.
        """
        if isinstance(v, str):
            result = _window_format(v, _return_timedelta=False)
            # Ensure we return a string
            if not isinstance(result, str):
                return str(result)
            return result

        msg = "Window must be a string."
        raise TypeError(msg)


class HumblChannelData(Data):
    """
    Data model for the Humbl Channel command, a Pandera.Polars Model.

    Parameters
    ----------
    date : Union[dt.date, dt.datetime], optional
        The date of the data point. Defaults to None.
    symbol : str, optional
        The stock symbol. Defaults to None.
    bottom_price : float, optional
        The bottom price in the Mandelbrot Channel. Defaults to None.
    recent_price : float, optional
        The most recent price within the Mandelbrot Channel. Defaults to None.
    top_price : float, optional
        The top price in the Mandelbrot Channel. Defaults to None.
    momentum_signal : float, optional
        The momentum signal value calculated based on the specified method.
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
    bottom_price: float = pa.Field(
        default=None,
        title="Bottom Price",
        description="The bottom price in the Mandelbrot Channel.",
    )
    recent_price: float = pa.Field(
        default=None,
        title="Recent Price",
        description="The most recent price within the Mandelbrot Channel.",
        alias="(close_price|recent_price|last_price)",
        regex=True,
    )
    top_price: float = pa.Field(
        default=None,
        title="Top Price",
        description="The top price in the Mandelbrot Channel.",
    )
    momentum_signal: pl.Int8 | None = pa.Field(
        default=None,
        title="Momentum Signal",
        description="The momentum signal value calculated based on the specified method.",
        nullable=True,
    )


class HumblChannelFetcher:
    """
    Fetcher for the Mandelbrot Channel command.

    Parameters
    ----------
    context_params : ToolboxQueryParams
        The context parameters for the toolbox query.
    command_params : HumblChannelQueryParams
        The command-specific parameters for the Mandelbrot Channel query.

    Attributes
    ----------
    context_params : ToolboxQueryParams
        Stores the context parameters passed during initialization.
    command_params : HumblChannelQueryParams
        Stores the command-specific parameters passed during initialization.
    equity_historical_data : pl.DataFrame
        The raw data extracted from the data provider, before transformation.

    Methods
    -------
    transform_query()
        Transform the command-specific parameters into a query.
    extract_data()
        Extracts the data from the provider and returns it as a Polars DataFrame.
    transform_data()
        Transforms the command-specific data according to the Mandelbrot Channel logic.
    fetch_data()
        Execute TET Pattern.

    Returns
    -------
    HumblObject
        results : HumblChannelData
            Serializable results.
        provider : Literal['fmp', 'intrinio', 'polygon', 'tiingo', 'yfinance']
            Provider name.
        warnings : Optional[List[Warning_]]
            List of warnings.
        chart : Optional[Chart]
            Chart object.
        context_params : ToolboxQueryParams
            Context-specific parameters.
        command_params : HumblChannelQueryParams
            Command-specific parameters.

    """

    def __init__(
        self,
        context_params: ToolboxQueryParams,
        command_params: HumblChannelQueryParams,
    ):
        """
        Initialize the HumblChannelFetcher with context and command parameters.

        Parameters
        ----------
        context_params : ToolboxQueryParams
            The context parameters for the toolbox query.
        command_params : HumblChannelQueryParams
            The command-specific parameters for the Mandelbrot Channel query.
        """
        self.context_params = context_params
        self.command_params = command_params
        self.warnings: list[Warning_] = []  # Initialize warnings list
        self.extra = {}  # Initialize extra dict

    @collect_warnings
    def transform_query(self):
        """
        Transform the command-specific parameters into a query.

        If command_params is not provided, it initializes a default HumblChannelQueryParams object.
        """
        if not self.command_params:
            # Set Default Arguments
            self.command_params = HumblChannelQueryParams()
        elif not isinstance(self.command_params, HumblChannelQueryParams):
            # If it's a dict, convert it to HumblChannelQueryParams
            self.command_params = HumblChannelQueryParams(
                **(self.command_params or {})
            )

        if self.command_params.yesterday_close:
            warnings.warn(
                "`recent_price` is representing yesterday's close price.",
                category=HumblDataWarning,
                stacklevel=1,
            )

    @collect_warnings
    async def extract_data(self):
        """
        Extract the data from the provider and returns it as a Polars DataFrame.

        Drops unnecessary columns like dividends and stock splits from the data.

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

    @collect_warnings
    def transform_data(self):
        """
        Transform the command-specific data according to the Mandelbrot Channel logic.

        Returns
        -------
        pl.DataFrame
            The transformed data as a Polars DataFrame
        """
        if self.command_params.historical is False:
            transformed_data = calc_humbl_channel(
                data=self.equity_historical_data,
                window=self.command_params.window,
                rv_adjustment=self.command_params.rv_adjustment,
                rv_method=self.command_params.rv_method,
                rv_grouped_mean=self.command_params.rv_grouped_mean,
                rs_method=self.command_params.rs_method,
                yesterday_close=self.command_params.yesterday_close,
            )
        else:
            transformed_data = calc_humbl_channel_historical_concurrent(
                data=self.equity_historical_data,
                window=self.command_params.window,
                rv_adjustment=self.command_params.rv_adjustment,
                rv_method=self.command_params.rv_method,
                rv_grouped_mean=self.command_params.rv_grouped_mean,
                rs_method=self.command_params.rs_method,
                yesterday_close=self.command_params.yesterday_close,
                use_processes=False,
            )

        # Apply momentum calculation if specified
        if self.command_params.momentum is not None:
            from humbldata.toolbox.technical.humbl_momentum.model import (
                calc_humbl_momentum,
            )

            momentum_data = calc_humbl_momentum(
                data=self.equity_historical_data,
                method=self.command_params.momentum,
                window=self.command_params.window,
            ).select(
                pl.col("date"), pl.col("symbol"), pl.col("momentum_signal")
            )
            transformed_data = transformed_data.join(
                momentum_data, on=["date", "symbol"], how="left"
            )
            if self.command_params.historical is False:
                # Append momentum to equity data only when not historical, the
                # momentum data is already joined to the transformed_data when
                # historical is True, so you can access the momentum data from
                # the transformed_data object. I am doing this becuase I need
                # equity_data to make a plot on frontend and if momentum is true
                # then I need the momentum data in the equity_data object for the plot
                # i am fixing this super quick in the middle of UX research so it can be improveed
                self.equity_historical_data = self.equity_historical_data.join(
                    momentum_data, on=["date", "symbol"], how="left"
                ).drop_nulls()
        else:
            momentum_data = None

        self.transformed_data = HumblChannelData(
            transformed_data.collect().drop_nulls()  ## HOTFIX - need to trace where coming from w/ unequal data
        ).lazy()

        if self.command_params.chart:
            self.chart = generate_plots(
                self.transformed_data,
                self.equity_historical_data,
                template=self.command_params.template,
                momentum_data=momentum_data,
            )
        else:
            self.chart = None

        self.transformed_data = serialize_lazyframe_to_ipc(
            self.transformed_data
        )
        self.equity_historical_data = serialize_lazyframe_to_ipc(
            self.equity_historical_data
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

        # Combine warnings from both sources
        all_warnings = self.context_params.warnings + self.warnings

        # Use the warnings collected during the process
        return HumblObject(
            results=self.transformed_data,
            equity_data=self.equity_historical_data,
            provider=self.context_params.provider,
            warnings=all_warnings,  # Use the warnings collected in this class
            chart=self.chart,
            context_params=self.context_params,
            command_params=self.command_params,
            extra=self.extra,  # pipe in extra from transform_data()
        )
