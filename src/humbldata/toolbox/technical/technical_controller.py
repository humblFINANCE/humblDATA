"""Context: Toolbox || **Category: Technical**.

A controller to manage and compile all of the technical indicator models
available. This will be passed as a `@property` to the `Toolbox()` class, giving
access to the technical module and its functions.
"""

from humbldata.core.standard_models.toolbox.technical.humbl_signal import HumblSignalQueryParams
from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.standard_models.toolbox.technical.humbl_channel import (
    HumblChannelQueryParams,
)
from humbldata.core.standard_models.toolbox.technical.humbl_momentum import (
    HumblMomentumQueryParams,
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
    humbl_channel(command_params: HumblChannelQueryParams)
        Calculate the rescaled range statistics.

    """

    def __init__(self, context_params: ToolboxQueryParams):
        self.context_params = context_params

    def humbl_momentum(self, **kwargs: HumblMomentumQueryParams):
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
            command_params : HumblMomentumQueryParams
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

            from humbldata.core.standard_models.toolbox.technical.humbl_momentum import (
                HumblMomentumFetcher,
            )

            # Instantiate the Fetcher with the query parameters
            fetcher = HumblMomentumFetcher(
                context_params=self.context_params,
                command_params=kwargs,
            )

            logger.debug("Fetching Momentum data")
            return fetcher.fetch_data()

        except Exception as e:
            logger.exception("Error calculating Momentum")
            msg = f"Failed to calculate Momentum: {e!s}"
            raise HumblDataError(msg) from e


    def humbl_signal(self, **kwargs: HumblSignalQueryParams):
        """
        Execute the HumblSignal command.

        Parameters
        ----------
        **kwargs : HumblSignalQueryParams
            The command-specific parameters.
        """
        try:
            logger.debug(
                "Initializing HumblSignal calculation with params: %s",
                kwargs,
            )

            from humbldata.core.standard_models.toolbox.technical.humbl_signal import HumblSignalFetcher

            # Instantiate the Fetcher with the query parameters
            fetcher = HumblSignalFetcher(
                context_params=self.context_params,
                command_params=kwargs,
            )

            logger.debug("Fetching HumblSignal data")
            return fetcher.fetch_data()

        except Exception as e:
            logger.exception("Error calculating HumblSignal")
            msg = f"Failed to calculate HumblSignal: {e!s}"
            raise HumblDataError(msg) from e
    def humbl_channel(self, **kwargs: HumblChannelQueryParams):
        """
        Calculate the Humbl Channel.

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
        yesterday_close : bool, optional
            Whether to calculate the ranges using the current price, or the
            use yesterday's close price. Defaults to False.
        historical : bool, optional
            Whether to calculate the Historical Mandelbrot Channel (over-time), and
            return a time-series of channels from the start to the end date. If
            False, the Mandelbrot Channel calculation is done aggregating all of the
            data into one observation. If True, then it will enable daily
            observations over-time. Defaults to False.
        momentum : Literal["shift", "log", "simple"] | None, optional
            Method to calculate momentum: 'shift' for simple shift, 'log' for
            logarithmic ROC, 'simple' for simple ROC. If None, momentum
            calculation is skipped.
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

            from humbldata.core.standard_models.toolbox.technical.humbl_channel import (
                HumblChannelFetcher,
            )

            # Instantiate the Fetcher with the query parameters
            fetcher = HumblChannelFetcher(
                context_params=self.context_params,
                command_params=kwargs,  # Pass kwargs directly, the Fetcher will handle conversion
            )

            logger.debug("Fetching Mandelbrot Channel data")
            return fetcher.fetch_data()

        except Exception as e:
            logger.exception("Error calculating Mandelbrot Channel")
            msg = f"Failed to calculate Mandelbrot Channel: {e!s}"
            raise HumblDataError(msg) from e
