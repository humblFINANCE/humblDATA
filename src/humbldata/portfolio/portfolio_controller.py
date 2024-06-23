
    """
    **Context: Portfolio**.

    The Portfolio Controller Module.
    """

    from humbldata.core.standard_models.portfolio import PortfolioQueryParams
    from humbldata.portfolio.analytics.analytics_controller import Analytics

    class Portfolio(PortfolioQueryParams):
        """
        A top-level Analytics controller for data analysis tools in `humblDATA`.

        This module serves as the primary controller, routing user-specified
        PortfolioQueryParams as core arguments that are used to fetch time series
        data.

        The `Portfolio` controller also gives access to all sub-modules and their
        functions.
        """

        def __init__(self, *args, **kwargs):
            """
            Initialize the Portfolio module.

            This method does not take any parameters and does not return anything.
            """
            super().__init__(*args, **kwargs)

        @property
        def analytics(self):
            """
            The Analytics submodule of the Portfolio controller.

            Access to all the Analytics indicators. When the Portfolio class is
            instantiated the parameters are initialized with the PortfolioQueryParams
            class, which hold all the fields needed for the context_params, like the
            symbol, interval, start_date, and end_date.
            """
            return Analytics(context_params=self)
    