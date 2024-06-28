"""Testing parameter/field validation for ToolboxQueryParams."""

from typing import get_args
import pytest

from humbldata.core.standard_models.toolbox import (
    ToolboxQueryParams,
)
from humbldata.core.utils.constants import OBB_EQUITY_PRICE_HISTORICAL_PROVIDERS


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
    """Test symbol validation and conversion to uppercase."""
    toolbox = ToolboxQueryParams(symbols=input)
    assert toolbox.symbols == expected


@pytest.mark.parametrize(
    "interval", ["1d", "5m", "10h", "2W", "3M", "1Q", "4Y", "30s"]
)
def test_toolbox_interval_validator(interval):
    """Test valid interval formats."""
    toolbox = ToolboxQueryParams(interval=interval)
    assert toolbox.interval == interval


@pytest.mark.parametrize(
    "interval", ["1x", "5", "10hh", "2WW", "3MM", "1QQ", "4YY", "30ss"]
)
def test_toolbox_interval_validator_error(interval):
    """Test invalid interval formats."""
    with pytest.raises(ValueError, match="Invalid interval format"):
        ToolboxQueryParams(interval=interval)


@pytest.mark.parametrize("date", ["2023-01-01", "1950-12-31", "2000-02-29"])
def test_toolbox_date_validator(date):
    """Test valid date formats."""
    toolbox = ToolboxQueryParams(start_date=date, end_date=date)
    assert toolbox.start_date == date
    assert toolbox.end_date == date


@pytest.mark.parametrize(
    "date", ["2023-13-01", "1950-00-31", "2000-02-33", "2023-01-32", "2023-1-1"]
)
def test_toolbox_date_validator_error(date):
    """Test invalid date formats."""
    with pytest.raises(ValueError, match="Invalid date format"):
        ToolboxQueryParams(start_date=date)
    with pytest.raises(ValueError, match="Invalid date format"):
        ToolboxQueryParams(end_date=date)


@pytest.mark.parametrize(
    "provider", list(get_args(OBB_EQUITY_PRICE_HISTORICAL_PROVIDERS))
)
def test_toolbox_provider_validator(provider):
    toolbox = ToolboxQueryParams(provider=provider)
    assert toolbox.provider == provider


@pytest.mark.parametrize(
    "provider", ["invalid_provider", "another_invalid", "yahoo_finance"]
)
def test_toolbox_provider_validator_error(provider):
    with pytest.raises(ValueError, match="Input should be"):
        ToolboxQueryParams(provider=provider)
