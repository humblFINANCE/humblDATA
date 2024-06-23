
    """
    Context: Portfolio || **Category: Analytics**.

    A controller to manage and compile all of the Analytics models
    available. This will be passed as a `@property` to the `Portfolio` class, giving
    access to the Analytics module and its functions.
    """

    from humbldata.core.standard_models.portfolio import PortfolioQueryParams

    class Analytics:
        """
        Module for all Analytics analysis.

        Attributes
        ----------
        standard_params : PortfolioQueryParams
            The standard query parameters for Portfolio data.

        Methods
        -------
        example_method(command_params: PortfolioTableQueryParams)
            Example method for the Analytics controller.
        """

        def __init__(self, context_params: PortfolioQueryParams):
            self.context_params = context_params

        def example_method(self, command_params: PortfolioTableQueryParams):
            """
            Example method for the Analytics controller.

            Parameters
            ----------
            command_params : PortfolioTableQueryParams
                The query parameters for the PortfolioTable command.

            Returns
            -------
            str
                Example result.
            """
            return "Example result"
    