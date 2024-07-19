"""
Mandelbrot Channel Standard Model.

Context: Toolbox || Category: Technical || Command: Mandelbrot Channel.

This module is used to define the QueryParams and Data model for the
Mandelbrot Channel command.
"""

import datetime as dt
from typing import Literal, TypeVar

import pandera.polars as pa
import polars as pl
from openbb import obb
from pydantic import Field, PrivateAttr, field_validator

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.utils.env import Env
from humbldata.core.utils.logger import log_start_end, setup_logger
from humbldata.toolbox.technical.mandelbrot_channel.model import (
    calc_mandelbrot_channel,
    calc_mandelbrot_channel_historical,
)
from humbldata.toolbox.technical.mandelbrot_channel.view import generate_plots
from humbldata.toolbox.toolbox_helpers import _window_format

env = Env()
Q = TypeVar("Q", bound=ToolboxQueryParams)
logger = setup_logger("MandelbrotChannelFetcher", level=env.LOGGER_LEVEL)

MANDELBROT_QUERY_DESCRIPTIONS = {
    "window": "The width of the window used for splitting the data into sections for detrending.",
    "rv_adjustment": "Whether to adjust the calculation for realized volatility. If True, the data is filtered to only include observations in the same volatility bucket that the stock is currently in.",
    "rv_method": "The method to calculate the realized volatility. Only need to define when rv_adjustment is True.",
    "rs_method": "The method to use for Range/STD calculation. THis is either, min, max or mean of all RS ranges per window. If not defined, just used the most recent RS window",
    "rv_grouped_mean": "Whether to calculate the the mean value of realized volatility over multiple window lengths",
    "live_price": "Whether to calculate the ranges using the current live price, or the most recent 'close' observation.",
    "historical": "Whether to calculate the Historical Mandelbrot Channel (over-time), and return a time-series of channels from the start to the end date. If False, the Mandelbrot Channel calculation is done aggregating all of the data into one observation. If True, then it will enable daily observations over-time.",
    "chart": "Whether to return a chart object.",
    "template": "The template/theme to use for the plotly figure.",
}


class MandelbrotChannelQueryParams(QueryParams):
    """
    QueryParams model for the Mandelbrot Channel command, a Pydantic v2 model.

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
    live_price : bool
        Whether to calculate the ranges using the current live price, or the
        most recent 'close' observation. Defaults to False.
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
    live_price: bool = Field(
        default=False,
        title="Live Price",
        description=MANDELBROT_QUERY_DESCRIPTIONS.get("live_price", ""),
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
    def window_format(cls, v: str) -> str:
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
            return _window_format(v, _return_timedelta=False)
        else:
            msg = "Window must be a string."
            raise ValueError(msg)


class MandelbrotChannelData(Data):
    """
    Data model for the Mandelbrot Channel command, a Pandera.Polars Model.

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


class MandelbrotChannelFetcher:
    """
    Fetcher for the Mandelbrot Channel command.

    Parameters
    ----------
    context_params : ToolboxQueryParams
        The context parameters for the toolbox query.
    command_params : MandelbrotChannelQueryParams
        The command-specific parameters for the Mandelbrot Channel query.

    Attributes
    ----------
    context_params : ToolboxQueryParams
        Stores the context parameters passed during initialization.
    command_params : MandelbrotChannelQueryParams
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
        results : MandelbrotChannelData
            Serializable results.
        provider : Literal['fmp', 'intrinio', 'polygon', 'tiingo', 'yfinance']
            Provider name.
        warnings : Optional[List[Warning_]]
            List of warnings.
        chart : Optional[Chart]
            Chart object.
        context_params : ToolboxQueryParams
            Context-specific parameters.
        command_params : MandelbrotChannelQueryParams
            Command-specific parameters.

    """

    def __init__(
        self,
        context_params: ToolboxQueryParams,
        command_params: MandelbrotChannelQueryParams,
    ):
        """
        Initialize the MandelbrotChannelFetcher with context and command parameters.

        Parameters
        ----------
        context_params : ToolboxQueryParams
            The context parameters for the toolbox query.
        command_params : MandelbrotChannelQueryParams
            The command-specific parameters for the Mandelbrot Channel query.
        """
        self.context_params = context_params
        self.command_params = command_params

    def transform_query(self):
        """
        Transform the command-specific parameters into a query.

        If command_params is not provided, it initializes a default MandelbrotChannelQueryParams object.
        """
        if not self.command_params:
            self.command_params = None
            # Set Default Arguments
            self.command_params: MandelbrotChannelQueryParams = (
                MandelbrotChannelQueryParams()
            )
        else:
            self.command_params: MandelbrotChannelQueryParams = (
                MandelbrotChannelQueryParams(**self.command_params)
            )

    def extract_data(self):
        """
        Extract the data from the provider and returns it as a Polars DataFrame.

        Drops unnecessary columns like dividends and stock splits from the data.

        Returns
        -------
        pl.DataFrame
            The extracted data as a Polars DataFrame.
        """
        self.equity_historical_data: pl.LazyFrame = (
            obb.equity.price.historical(
                symbol=self.context_params.symbols,
                start_date=self.context_params.start_date,
                end_date=self.context_params.end_date,
                provider=self.context_params.provider,
                adjustment="splits_and_dividends",
                # add kwargs
            )
            .to_polars()
            .lazy()
        ).drop(["dividend", "split_ratio"])  # TODO: drop `capital_gains` col

        if len(self.context_params.symbols) == 1:
            self.equity_historical_data = (
                self.equity_historical_data.with_columns(
                    symbol=pl.lit(self.context_params.symbols[0])
                )
            )
        return self

    def transform_data(self):
        """
        Transform the command-specific data according to the Mandelbrot Channel logic.

        Returns
        -------
        pl.DataFrame
            The transformed data as a Polars DataFrame
        """
        if self.command_params.historical is False:
            transformed_data = calc_mandelbrot_channel(
                data=self.equity_historical_data,
                window=self.command_params.window,
                rv_adjustment=self.command_params.rv_adjustment,
                rv_method=self.command_params.rv_method,
                rv_grouped_mean=self.command_params.rv_grouped_mean,
                rs_method=self.command_params.rs_method,
                live_price=self.command_params.live_price,
            )
        else:
            transformed_data = calc_mandelbrot_channel_historical(
                data=self.equity_historical_data,
                window=self.command_params.window,
                rv_adjustment=self.command_params.rv_adjustment,
                rv_method=self.command_params.rv_method,
                rv_grouped_mean=self.command_params.rv_grouped_mean,
                rs_method=self.command_params.rs_method,
                live_price=self.command_params.live_price,
            )

        self.transformed_data = MandelbrotChannelData(
            transformed_data.collect().drop_nulls()  ## HOTFIX - need to trace where coming from w/ unequal data
        ).lazy()

        if self.command_params.chart:
            self.chart = generate_plots(
                self.transformed_data,
                self.equity_historical_data,
                template=self.command_params.template,
            )
        else:
            self.chart = None

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
        pl.DataFrame
            The transformed data as a Polars DataFrame, ready for further analysis
            or visualization.
        """
        self.transform_query()
        self.extract_data()
        self.transform_data()

        if not hasattr(self.context_params, "warnings"):
            self.context_params.warnings = []

        return HumblObject(
            results=self.transformed_data,
            provider=self.context_params.provider,
            equity_data=self.equity_historical_data.serialize(),
            warnings=self.context_params.warnings,
            chart=self.chart,
            context_params=self.context_params,
            command_params=self.command_params,
        )
