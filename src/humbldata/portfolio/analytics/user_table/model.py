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
    # Setup Toolbox
    # TODO: make different toolboxes for different user_roles
    # TODO: have different date collection for different users
    toolbox = Toolbox(
        symbol=self.context_params.symbol,
        interval="1d",
        start_date="2020-01-01",
        end_date="2024-01-01",
    )

    # Get last_price from OpenBB
    last_prices_df = get_latest_price(
        symbol=self.context_params.symbol,
        provider=self.context_params.provider,
    )
    # Get Mandelbrot Data
    mandelbrot_df = toolbox.technical.mandelbrot_channel(
        window="1m", historical=True
    )

    # Get sector Data
    sectors_df = get_sector(symbols=self.context_params.symbol)
