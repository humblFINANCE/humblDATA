import pytest

from humbldata.core.standard_models.toolbox import (
    ToolboxQueryParams,
)


@pytest.mark.parametrize(
    ("input", "expected"),
    [
        ("aapl", ["AAPL"]),
        ("aapl,msft", ["AAPL", "MSFT"]),
        ("aapl, msft", ["AAPL", "MSFT"]),
        ("AAPL,msft, GOOG", ["AAPL", "MSFT", "GOOG"]),
        (["aapl"], ["AAPL"]),
        (["aapl", "msft"], ["AAPL", "MSFT"]),
        (["aapl", "MSFT"], ["AAPL", "MSFT"]),
        (["aapl", "msFT", "amd", "TSla"], ["AAPL", "MSFT", "AMD", "TSLA"]),
    ],
)
def test_toolbox_symbol_validator(input, expected):
    toolbox = ToolboxQueryParams(symbol=input)
    assert toolbox.symbol == expected
