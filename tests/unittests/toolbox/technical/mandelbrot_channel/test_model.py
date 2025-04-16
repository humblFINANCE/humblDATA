import polars as pl
import pytest

from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.toolbox.technical.humbl_channel.model import (
    calc_humbl_channel,
    calc_humbl_channel_historical,
)


@pytest.mark.skip("validation will occur in the Fetcher")
def test_calc_humbl_channel_invalid_data():
    """Testing Input Validation"""
    with pytest.raises(HumblDataError):
        result = calc_humbl_channel(data=pl.DataFrame().to_pandas())


## The internal functions used in the model are tested in the helpers.py file
## The model is tested with all the function in the integration tests folder.
