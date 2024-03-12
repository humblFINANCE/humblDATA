"""Context: Toolbox || **Category: Technical**.

A controller to manage and compile all of the technical indicator models
available. This will be passed as a `@property` to the `Toolbox()` class, giving
access to the technical module and its functions.
"""

from humbldata.core.standard_models.toolbox.technical.mandelbrotchannel import (
    MandelbrotChannelQueryParams,
)


class Technical:
    """
    Module for all technical analysis.

    Attributes
    ----------
    standard_params : ToolboxQueryParams
        The standard query parameters for toolbox data.

    Methods
    -------
    mandelbrot_channel(command_params: MandelbrotChannelQueryParams)
        Calculate the rescaled range statistics.

    """

    def __init__(self, context_params):
        self._context_params = context_params

    def mandelbrot_channel(self, command_params: MandelbrotChannelQueryParams):
        """
        Calculate the rescaled range statistics.

        Explain the math...
        """
        from humbldata.core.standard_models.toolbox.technical.mandelbrotchannel import (
            MandelbrotChannelFetcher,
        )

        # Instantiate the Fetcher with the query parameters
        fetcher = MandelbrotChannelFetcher(self._context_params, command_params)

        # Use the fetcher to get the data
        return fetcher.fetch_data()


a
