"""Context: Toolbox || **Category: Technical**.

A controller to manage and compile all of the technical indicator models
available. This will be passed as a `@property` to the `Toolbox()` class, giving
access to the technical module and its functions.
"""

from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.standard_models.toolbox.technical.mandelbrot_channel import (
    MandelbrotChannelQueryParams,
)
from humbldata.core.standard_models.toolbox.technical.momentum import (
    MomentumQueryParams,
)
from humbldata.core.utils.logger import setup_logger

logger = setup_logger(__name__)


class Technical:
    """
    Module for all technical analysis.

    Attributes
    ----------
    context_params : ToolboxQueryParams
        The standard query parameters for toolbox data.

    Methods
    -------
    mandelbrot_channel(command_params: MandelbrotChannelQueryParams)
        Calculate the rescaled range statistics.

    """

    def __init__(self, context_params: ToolboxQueryParams):
        self.context_params = context_params

    def momentum(self, **kwargs: MomentumQueryParams):
        """
        Execute the Momentum command.

        Parameters
        ----------
        method : Literal['log', 'simple', 'shift'], optional
            Method to calculate momentum:
            - 'log': Logarithmic rate of change
            - 'simple': Simple rate of change (percentage change)
            - 'shift': Simple time series shift with binary signal
            Default is 'log'.

        window : str, optional
            Window to calculate momentum over. Default is "1d".

        chart : bool, optional
            Whether to generate and return a visualization chart.
            Default is False.

        Returns
        -------
        HumblObject
            results : MomentumData
                DataFrame containing:
                - date: Date of observation
                - symbol: Stock symbol
                - momentum: Momentum value (for log/simple methods)
                - shifted: Shifted price (for shift method)
                - momentum_signal: Binary signal (for shift method)
            provider : str
                Data provider name
            warnings : list
                Any warnings generated during calculation
            chart : Optional[Chart]
                Visualization if chart=True
            context_params : ToolboxQueryParams
                Original context parameters
            command_params : MomentumQueryParams
                Command parameters used
            extra : dict
                Additional metadata

        Raises
        ------
        HumblDataError
            If calculation fails or required data is missing
        """
        try:
            logger.debug(
                "Initializing Momentum calculation with params: %s",
                kwargs,
            )

            from humbldata.core.standard_models.toolbox.technical.momentum import (
                MomentumFetcher,
            )

            # Instantiate the Fetcher with the query parameters
            fetcher = MomentumFetcher(
                context_params=self.context_params,
                command_params=kwargs,
            )

            logger.debug("Fetching Momentum data")
            return fetcher.fetch_data()

        except Exception as e:
            logger.exception("Error calculating Momentum")
            msg = f"Failed to calculate Momentum: {e!s}"
            raise HumblDataError(msg) from e

    def mandelbrot_channel(self, **kwargs: MandelbrotChannelQueryParams):
        """
        Calculate the Mandelbrot Channel.

        Parameters
        ----------
        window : str, optional
            The width of the window used for splitting the data into sections for
            detrending. Defaults to "1mo".
        rv_adjustment : bool, optional
            Whether to adjust the calculation for realized volatility. If True, the
            data is filtered to only include observations in the same volatility bucket
            that the stock is currently in. Defaults to True.
        rv_method : str, optional
            The method to calculate the realized volatility. Only need to define
            when rv_adjustment is True. Defaults to "std".
        rs_method : Literal["RS", "RS_min", "RS_max", "RS_mean"], optional
            The method to use for Range/STD calculation. This is either min, max
            or mean of all RS ranges per window. If not defined, just used the
            most recent RS window. Defaults to "RS".
        rv_grouped_mean : bool, optional
            Whether to calculate the mean value of realized volatility over
            multiple window lengths. Defaults to False.
        live_price : bool, optional
            Whether to calculate the ranges using the current live price, or the
            most recent 'close' observation. Defaults to False.
        historical : bool, optional
            Whether to calculate the Historical Mandelbrot Channel (over-time), and
            return a time-series of channels from the start to the end date. If
            False, the Mandelbrot Channel calculation is done aggregating all of the
            data into one observation. If True, then it will enable daily
            observations over-time. Defaults to False.
        chart : bool, optional
            Whether to return a chart object. Defaults to False.
        template : str, optional
            The template/theme to use for the plotly figure. Defaults to "humbl_dark".

        Returns
        -------
        HumblObject
            An object containing the Mandelbrot Channel data and metadata.
        """
        try:
            logger.debug(
                "Initializing Mandelbrot Channel calculation with params: %s",
                kwargs,
            )

            from humbldata.core.standard_models.toolbox.technical.mandelbrot_channel import (
                MandelbrotChannelFetcher,
            )

            # Instantiate the Fetcher with the query parameters
            fetcher = MandelbrotChannelFetcher(
                context_params=self.context_params,
                command_params=kwargs,  # Pass kwargs directly, the Fetcher will handle conversion
            )

            logger.debug("Fetching Mandelbrot Channel data")
            return fetcher.fetch_data()

        except Exception as e:
            logger.exception("Error calculating Mandelbrot Channel")
            msg = f"Failed to calculate Mandelbrot Channel: {e!s}"
            raise HumblDataError(msg) from e
