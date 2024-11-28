"""Testing parameter/field validation for ToolboxQueryParams."""

import datetime
from datetime import date
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
        (["aapl", " "], ["AAPL"]),
    ],
)
def test_toolbox_symbol_validator(input, expected):
    """Test symbol validation and conversion to uppercase."""
    toolbox = ToolboxQueryParams(symbols=input)
    assert toolbox.symbols == expected


@pytest.mark.parametrize(
    "invalid_input",
    [
        123,
        ["aapl", 123],
        ["aapl", None],
    ],
)
def test_toolbox_symbol_validator_error(invalid_input):
    """Test invalid symbol inputs."""
    with pytest.raises((TypeError, AttributeError)):
        ToolboxQueryParams(symbols=invalid_input)


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


@pytest.mark.parametrize(
    "input_date, expected_date",
    [
        ("2023-01-01", datetime.date(2023, 1, 1)),
        ("1950-12-31", datetime.date(1950, 12, 31)),
        ("2000-02-29", datetime.date(2000, 2, 29)),
        (datetime.date(2023, 1, 1), datetime.date(2023, 1, 1)),
        (datetime.date(1950, 12, 31), datetime.date(1950, 12, 31)),
        (datetime.date(2000, 2, 29), datetime.date(2000, 2, 29)),
    ],
)
def test_toolbox_date_type(input_date, expected_date):
    """Test that both string and datetime.date inputs are correctly handled and returned as datetime.date objects."""
    toolbox = ToolboxQueryParams(
        start_date=input_date, end_date=input_date, membership="admin"
    )

    assert isinstance(toolbox.start_date, date)
    assert isinstance(toolbox.end_date, date)
    assert toolbox.start_date == expected_date
    assert toolbox.end_date == expected_date


@pytest.mark.parametrize(
    "invalid_date",
    [
        "12-31-2023",  # MM-DD-YYYY
        "2023/01/01",  # YYYY/MM/DD
        "23-01-01",  # YY-MM-DD
        "Jan 1, 2023",  # Month Day, Year
        "2023.01.01",  # YYYY.MM.DD
        "2023-00-01",  # Invalid month (00)
        "2023-13-01",  # Invalid month (13)
        "2023-01-00",  # Invalid day (00)
        "2023-04-31",  # Invalid day (31 for April)
        "2023-02-29",  # Invalid day (29 for non-leap year)
        "2023-06-31",  # Invalid day (31 for June)
        datetime.date(23, 1, 1),  # YY-MM-DD as date object
        datetime.date(1949, 12, 31),  # Invalid date before 1950
    ],
)
def test_toolbox_date_validator_error(invalid_date):
    """Test that invalid date formats raise appropriate errors."""
    with pytest.raises((ValueError, TypeError)):
        ToolboxQueryParams(
            start_date=invalid_date, end_date=invalid_date, membership="admin"
        )


import pytest
from datetime import datetime, timedelta


@pytest.mark.parametrize(
    "membership, start_date, expected_start_date",
    [
        (
            "anonymous",
            datetime(2022, 8, 20).date(),
            datetime(2023, 1, 1).date(),
        ),
        (
            "humblPEON",
            datetime(2021, 1, 5).date(),
            datetime(2022, 1, 1).date(),
        ),
        (
            "humblPREMIUM",
            datetime(2018, 6, 10).date(),
            datetime(2019, 1, 2).date(),
        ),
        (
            "humblPOWER",
            datetime(2001, 1, 1).date(),
            datetime(2004, 1, 6).date(),
        ),
        (
            "humblPERMANENT",
            datetime(1993, 7, 15).date(),
            datetime(1994, 10, 5).date(),
        ),
        (
            "admin",
            datetime(1950, 1, 1).date(),
            datetime(1950, 1, 1).date(),
        ),
    ],
)
def test_validate_start_date(membership, start_date, expected_start_date):
    """
    Test that the start_date is correctly adjusted based on the membership.

    All start_dates that are passed are earlier than the membership level allows
    """
    end_date = datetime(2024, 1, 1).date()
    toolbox = ToolboxQueryParams(
        start_date=start_date, end_date=end_date, membership=membership
    )

    assert (
        toolbox.start_date == expected_start_date
    ), f"For {membership} membership, start_date should be adjusted to {expected_start_date}"
    assert toolbox.end_date == end_date, "End date should remain unchanged"


def test_toolbox_default_values():
    """Test default values for ToolboxQueryParams."""
    expected_end_date = datetime.now().date()

    # calculate admin `start_date`
    expected_start_date = expected_end_date - timedelta(days=365)

    params = ToolboxQueryParams()
    assert params.symbols == None
    assert params.provider == "yfinance"
    assert params.interval == "1d"
    assert params.start_date == expected_start_date
    assert params.end_date == expected_end_date


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
