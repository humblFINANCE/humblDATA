
"""Context: Toolbox || **Category: Fundamental**.

A controller to manage and compile all of the Fundamental models
available in the `toolbox` context. This will be passed as a
`@property` to the `toolbox()` class, giving access to the
Fundamental module and its functions.
"""
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.standard_models.toolbox.fundamental.humbl_compass import (
    HumblCompassQueryParams,
)


class Fundamental:
    """
    Module for all Fundamental analysis.

    Attributes
    ----------
    context_params : ToolboxQueryParams
        The standard query parameters for toolbox data.

    Methods
    -------
    humbl_compass(command_params: HumblCompassQueryParams)
        Execute the HumblCompass command.

    """

    def __init__(self, context_params: ToolboxQueryParams):
        self.context_params = context_params

    def humbl_compass(self, **kwargs: HumblCompassQueryParams):
        """
        Execute the HumblCompass command.

        Explain the functionality...
        """
        from humbldata.core.standard_models.toolbox.fundamental.humbl_compass import (
            HumblCompassFetcher,
        )

        # Instantiate the Fetcher with the query parameters
        fetcher = HumblCompassFetcher(
            context_params=self.context_params, command_params=kwargs
        )

        # Use the fetcher to get the data
        return fetcher.fetch_data()
