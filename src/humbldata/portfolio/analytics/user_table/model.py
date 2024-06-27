"""
**Context: Portfolio || Category: Analytics || Command: user_table**.

The user_table Command Module.
"""

from humbldata.core.utils.openbb_helpers import get_latest_price, get_sector
from humbldata.toolbox.toolbox_controller import Toolbox


def user_table_engine(self):
    """
    Context: Portfolio || Category: Analytics ||| **Command: user_table**.

    Execute the logic to collect all necessary information for the
    user_table command. The data collected is to be used on the `dashboard/portfolio`
    page in humblFINANCE.

    Parameters
    ----------
    self : UserTableFetcher
        The instance of UserTableFetcher.

    Returns
    -------
    None
        This function does not return a value.
    """
    # Setup Toolbox and run `aggregate_user_table_data()`
