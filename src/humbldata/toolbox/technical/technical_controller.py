"""Context: Toolbox || **Category: Technical**.

A controller to manage and compile all of the technical indicator models
available. This will be passed as a `@property` to the `Toolbox()` class, giving
access to the technical module and its functions.
"""

from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.standard_models.toolbox.technical.mandelbrot_channel import (
    MandelbrotChannelQueryParams,
)


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
        from humbldata.core.standard_models.toolbox.technical.mandelbrot_channel import (
            MandelbrotChannelFetcher,
        )

        # Instantiate the Fetcher with the query parameters
        fetcher = MandelbrotChannelFetcher(
            context_params=self.context_params, command_params=kwargs
        )

        # Use the fetcher to get the data
        return fetcher.fetch_data()
