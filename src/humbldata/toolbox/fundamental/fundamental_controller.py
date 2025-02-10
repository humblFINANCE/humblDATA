"""Context: Toolbox || **Category: Fundamental**.

A controller to manage and compile all of the Fundamental models
available in the `toolbox` context. This will be passed as a
`@property` to the `toolbox()` class, giving access to the
Fundamental module and its functions.
"""

from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.standard_models.toolbox.fundamental.humbl_compass import (
    HumblCompassQueryParams,
)
from humbldata.core.standard_models.toolbox.fundamental.humbl_compass_backtest import (
    HumblCompassBacktestQueryParams,
)
from humbldata.core.utils.env import Env
from humbldata.core.utils.logger import setup_logger

env = Env()
logger = setup_logger("FundamentalController", env.LOGGER_LEVEL)


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

    def humbl_compass_backtest(self, **kwargs: HumblCompassBacktestQueryParams):
        """
        Execute the HumblCompassBacktest command.

        Parameters
        ----------
        **kwargs : HumblCompassBacktestQueryParams
            The command-specific parameters.
        """
        try:
            logger.debug(
                "Initializing HumblCompassBacktest calculation with params: %s",
                kwargs,
            )

            from humbldata.core.standard_models.toolbox.fundamental.humbl_compass_backtest import (
                HumblCompassBacktestFetcher,
            )

            # Instantiate the Fetcher with the query parameters
            fetcher = HumblCompassBacktestFetcher(
                context_params=self.context_params,
                command_params=kwargs,
            )

            logger.debug("Fetching HumblCompassBacktest data")
            return fetcher.fetch_data()

        except Exception as e:
            logger.exception("Error calculating HumblCompassBacktest")
            msg = f"Failed to calculate HumblCompassBacktest: {e!s}"
            raise HumblDataError(msg) from e

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

        # Convert kwargs to query params and instantiate fetcher.
        command_params = HumblCompassQueryParams(**kwargs)
        fetcher = HumblCompassFetcher(
            context_params=self.context_params, command_params=command_params
        )
        # Get the result which is a HumblObject (with its serialized data),
        # and which also has stored raw transformed data in fetcher._raw_transformed_df.
        result = fetcher.fetch_data()

        # Capture the raw transformed data needed for backtest.
        raw_transformed = fetcher._raw_transformed_df

        # Attach a backtest method to the result.
        def backtest(**backtest_kwargs):
            from humbldata.core.standard_models.toolbox.fundamental.humbl_compass_backtest import (
                HumblCompassBacktestFetcher,
                HumblCompassBacktestQueryParams,
            )

            # Use backtest_kwargs to create backtest command parameters.
            bt_params = HumblCompassBacktestQueryParams(**backtest_kwargs)
            bt_fetcher = HumblCompassBacktestFetcher(
                context_params=self.context_params,
                command_params=bt_params,
                compass_data=raw_transformed,
            )
            return bt_fetcher.fetch_data()

        # Now you can chain: result.backtest(symbols=["SPY"])
        result.backtest = backtest
        return result
