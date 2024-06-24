"""Context: Portfolio || **Category: Analytics**.

A controller to manage and compile all of the analytics models
available in the `portfolio` context. This will be passed as a
`@property` to the `portfolio()` class, giving access to the
analytics module and its functions.
"""
from humbldata.core.standard_models.portfolio import PortfolioQueryParams
from humbldata.core.standard_models.portfolio.analytics.user table import (
    user tableQueryParams,
)


class analytics:
    """
    Module for all analytics analysis.

    Attributes
    ----------
    context_params : PortfolioQueryParams
        The standard query parameters for portfolio data.

    Methods
    -------
    user table(command_params: user tableQueryParams)
        Execute the user table command.

    """

    def __init__(self, context_params: PortfolioQueryParams):
        self.context_params = context_params

    def user table(self, **kwargs: user tableQueryParams):
        """
        Execute the user table command.

        Explain the functionality...
        """
        from humbldata.core.standard_models.portfolio.analytics.user table import (
            User tableFetcher,
        )

        # Instantiate the Fetcher with the query parameters
        fetcher = User tableFetcher(
            context_params=self.context_params, command_params=kwargs
        )

        # Use the fetcher to get the data
        return fetcher.fetch_data()