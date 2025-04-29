"""Context: Portfolio || **Category: Analytics**.

A controller to manage and compile all of the Analytics models
available in the `portfolio` context. This will be passed as a
`@property` to the `portfolio()` class, giving access to the
Analytics module and its functions.
"""

from humbldata.core.standard_models.portfolio import PortfolioQueryParams
from humbldata.core.standard_models.portfolio.analytics.watchlist_table import (
    WatchlistTableQueryParams,
)


class Analytics:
    """
    Module for all Analytics analysis.

    Attributes
    ----------
    context_params : PortfolioQueryParams
        The standard query parameters for portfolio data.

    Methods
    -------
    watchlist_table(command_params: WatchlistTableQueryParams)
        Execute the WatchlistTable command.

    """

    def __init__(self, context_params: PortfolioQueryParams):
        self.context_params = context_params

    def watchlist_table(self, **kwargs: WatchlistTableQueryParams):
        """
        Execute the WatchlistTable command.

        Explain the functionality...
        """
        from humbldata.core.standard_models.portfolio.analytics.watchlist_table import (
            WatchlistTableFetcher,
        )

        # Instantiate the Fetcher with the query parameters
        fetcher = WatchlistTableFetcher(
            context_params=self.context_params, command_params=kwargs
        )

        # Use the fetcher to get the data
        return fetcher.fetch_data()
