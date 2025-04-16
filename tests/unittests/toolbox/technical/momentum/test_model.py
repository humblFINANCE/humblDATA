from datetime import datetime, timedelta
from typing import Literal

import polars as pl
import pytest

from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.toolbox.technical.humbl_momentum.model import (
    _calc_log_roc,
    _calc_shift,
    _calc_simple_roc,
)


@pytest.fixture
def sample_data():
    """Create sample data with two symbols and known values for testing."""
    dates = [datetime(2024, 1, 1) + timedelta(days=x) for x in range(5)]

    data = pl.DataFrame(
        {
            "date": dates * 2,
            "symbol": ["AAPL"] * 5 + ["MSFT"] * 5,
            "close": [
                100.0,
                110.0,
                105.0,
                115.0,
                120.0,  # AAPL
                50.0,
                52.0,
                48.0,
                53.0,
                55.0,  # MSFT
            ],
        }
    ).lazy()

    return data


@pytest.mark.parametrize(
    "symbol,expected_values",
    [
        ("AAPL", [None, None, 0.0488, 0.0445, 0.1335]),
        ("MSFT", [None, None, -0.0408, 0.0190, 0.1361]),
    ],
    ids=["AAPL", "MSFT"],
)
def test_calc_log_roc(sample_data, symbol, expected_values):
    """Test log ROC calculation for expected values."""
    result = _calc_log_roc(sample_data, window_days=2).collect()
    symbol_data = result.filter(pl.col("symbol") == symbol)
    momentum_values = symbol_data.get_column("momentum").to_list()

    # Check first two values are null (due to window)
    assert all(pl.Series(momentum_values[:2]).is_null())

    # Check remaining values match expected (within tolerance)
    for actual, expected in zip(momentum_values[2:], expected_values[2:]):
        assert abs(actual - expected) < 0.001


@pytest.mark.parametrize(
    "symbol,expected_values",
    [
        ("AAPL", [None, None, 0.05, 0.0455, 0.1429]),
        ("MSFT", [None, None, -0.04, 0.0192, 0.1458]),
    ],
    ids=["AAPL", "MSFT"],
)
def test_calc_simple_roc(sample_data, symbol, expected_values):
    """Test simple ROC calculation for expected values."""
    result = _calc_simple_roc(sample_data, window_days=2).collect()
    symbol_data = result.filter(pl.col("symbol") == symbol)
    momentum_values = symbol_data.get_column("momentum").to_list()

    # Check first two values are null (due to window)
    assert all(pl.Series(momentum_values[:2]).is_null())

    # Check remaining values match expected (within tolerance)
    for actual, expected in zip(momentum_values[2:], expected_values[2:]):
        assert abs(actual - expected) < 0.001


@pytest.mark.parametrize(
    "symbol,expected_signal,expected_shift",
    [
        ("AAPL", [None, None, 1, 1, 1], [None, None, 100.0, 110.0, 105.0]),
        ("MSFT", [None, None, 0, 1, 1], [None, None, 50.0, 52.0, 48.0]),
    ],
    ids=["AAPL", "MSFT"],
)
def test_calc_shift(sample_data, symbol, expected_signal, expected_shift):
    """Test shift calculation and signal generation."""
    result = _calc_shift(sample_data, window_days=2).collect()
    symbol_data = result.filter(pl.col("symbol") == symbol)

    # Check momentum signals
    signals = symbol_data.get_column("momentum_signal").to_list()
    assert signals[:2] == [None, None]  # First two should be null
    assert signals[2:] == expected_signal[2:]

    # Check shifted values
    shifts = symbol_data.get_column("shifted").to_list()
    assert all(pl.Series(shifts[:2]).is_null())  # First two should be null
    for actual, expected in zip(shifts[2:], expected_shift[2:]):
        assert abs(actual - expected) < 0.001


@pytest.mark.parametrize(
    "func,name",
    [
        (_calc_log_roc, "log_roc"),
        (_calc_simple_roc, "simple_roc"),
        (_calc_shift, "shift"),
    ],
    ids=["log_roc", "simple_roc", "shift"],
)
def test_error_handling(func, name):
    """Test error handling for invalid input data."""
    invalid_data = pl.DataFrame(
        {
            "date": [datetime(2024, 1, 1)],
            "symbol": ["AAPL"],
            # Missing 'close' column
        }
    ).lazy()

    with pytest.raises(Exception):
        func(invalid_data).collect()


@pytest.mark.parametrize(
    "func,name,expected_columns",
    [
        (_calc_log_roc, "log_roc", ["date", "symbol", "close", "momentum"]),
        (
            _calc_simple_roc,
            "simple_roc",
            ["date", "symbol", "close", "momentum"],
        ),
        (
            _calc_shift,
            "shift",
            ["date", "symbol", "close", "shifted", "momentum_signal"],
        ),
    ],
    ids=["log_roc", "simple_roc", "shift"],
)
def test_multiple_symbols(func, name, expected_columns, sample_data):
    """Test that functions handle multiple symbols correctly."""
    result = func(sample_data).collect()

    # Check that both symbols are present in result
    unique_symbols = result.get_column("symbol").unique().to_list()
    assert set(unique_symbols) == {"AAPL", "MSFT"}

    # Check that each symbol has correct number of rows
    for symbol in ["AAPL", "MSFT"]:
        symbol_count = result.filter(pl.col("symbol") == symbol).height
        assert symbol_count == 5  # Number of dates in sample data

    # Check that all expected columns are present
    assert all(col in result.columns for col in expected_columns)
