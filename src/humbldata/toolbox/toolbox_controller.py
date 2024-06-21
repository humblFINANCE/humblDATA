"""
**Context: Toolbox**.

The Toolbox Controller Module.
"""

from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.toolbox.technical.technical_controller import Technical


class Toolbox(ToolboxQueryParams):
    """

    A top-level <context> controller for data analysis tools in `humblDATA`.

    This module serves as the primary controller, routing user-specified
    ToolboxQueryParams as core arguments that are used to fetch time series
    data.

    The `Toolbox` controller also gives access to all sub-modules adn their
    functions.

    It is designed to facilitate the collection of data across various types such as
    stocks, options, or alternative time series by requiring minimal input from the user.

    Submodules
    ----------
    The `Toolbox` controller is composed of the following submodules:

    - `technical`:
    - `quantitative`:
    - `fundamental`:

    Parameters
    ----------
    symbol : str
        The symbol or ticker of the stock.
    interval : str, optional
        The interval of the data. Defaults to '1d'.
    start_date : str
        The start date for the data query.
    end_date : str
        The end date for the data query.
    provider : str, optional
        The provider to use for the data query. Defaults to 'yfinance'.

    Parameter Notes
    -----
    The parameters (`symbol`, `interval`, `start_date`, `end_date`)
    are the `ToolboxQueryParams`. They are used for data collection further
    down the pipeline in other commands. Intended to execute operations on core
    data sets. This approach enables composable and standardized querying while
    accommodating data-specific collection logic.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the Toolbox module.

        This method does not take any parameters and does not return anything.
        """
        super().__init__(*args, **kwargs)

    @property
    def technical(self):
        """
        The technical submodule of the Toolbox controller.

        Access to all the technical indicators. WHen the Toolbox class is
        instatiated the parameters are initialized with the ToolboxQueryParams
        class, which hold all the fields needed for the context_params, like the
        symbol, interval, start_date, and end_date.
        """
        return Technical(context_params=self)
