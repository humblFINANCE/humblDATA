from unittest.mock import patch

import polars as pl
import pytest
from openbb_core.app.model.abstract.error import OpenBBError

from humbldata.core.utils.openbb_helpers import get_latest_price, obb_login

pytestmark = pytest.mark.skip(reason="Need to figure out OBB Login")

# skip_if_not_logged_in = pytest.mark.skipif(
#     not obb_login(), reason="Login failed"
# )

# Need to find a way to test making web requests without actually making them,
# potentially mock the obb function call


# @skip_if_not_logged_in
# @pytest.mark.skip()
@pytest.mark.parametrize(
    "symbol",
    ["AAPL", ["AAPL", "GOOGL"]],
)
def test_get_latest_price(symbol):
    """Test the get_recent_price function."""
    prices = get_latest_price(symbol, "fmp")
    assert isinstance(prices, pl.LazyFrame)


@pytest.mark.skip()
def test_get_latest_price_with_invalid_symbol():
    """Test that get_recent_price raises a ValueError when an invalid symbol is passed."""
    with pytest.raises(OpenBBError):
        get_latest_price("")
