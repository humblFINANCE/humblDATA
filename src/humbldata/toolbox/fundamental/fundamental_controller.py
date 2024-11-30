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

    def humbl_compass(self, **kwargs):
        """
        Execute the HumblCompass command.

        Parameters
        ----------
        country : str
            The country or group of countries to analyze
        recommendations : bool, optional
            Whether to include investment recommendations based on the HUMBL regime
        chart : bool, optional
            Whether to return a chart object
        template : str, optional
            The template/theme to use for the plotly figure
        z_score : str, optional
            The time window for z-score calculation

        Returns
        -------
        HumblObject
            The HumblObject containing the transformed data and metadata
        """
        from humbldata.core.standard_models.toolbox.fundamental.humbl_compass import (
            HumblCompassFetcher,
            HumblCompassQueryParams,
        )

        # Convert kwargs to HumblCompassQueryParams
        command_params = HumblCompassQueryParams(**kwargs)

        # Instantiate the Fetcher with the query parameters
        fetcher = HumblCompassFetcher(
            context_params=self.context_params, command_params=command_params
        )

        # Use the fetcher to get the data
        return fetcher.fetch_data()
