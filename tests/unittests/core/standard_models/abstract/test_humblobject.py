import pytest
from pydantic import ValidationError

from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.toolbox import ToolboxQueryParams


def test_humblobject_params():
    assert isinstance(HumblObject().context_params, ToolboxQueryParams)
    assert HumblObject().command_params.__name__ == "QueryParams"


@pytest.mark.parametrize(
    ("provider_input", "expected_error"),
    [
        ("yfinance", None),
        ("fmp", None),
        ("intrinio", None),
        (2, ValidationError),
    ],
)
def test_humblobject_provider(provider_input, expected_error):
    if expected_error:
        with pytest.raises(expected_error):
            HumblObject(provider=provider_input).provider
    else:
        assert HumblObject(provider=provider_input).provider == provider_input
