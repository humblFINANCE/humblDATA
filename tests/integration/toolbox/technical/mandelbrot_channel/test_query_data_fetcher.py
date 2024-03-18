import datetime

import polars as pl
import pytest
from h11 import Data

from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.standard_models.toolbox.technical.mandelbrotchannel import (
    MandelbrotChannelData,
    MandelbrotChannelFetcher,
    MandelbrotChannelQueryParams,
)


@pytest.mark.parametrize(
    ("input_window", "expected_window"),
    [
        ("1 day", "1d"),
        ("60 days", "60d"),
        ("1 mon", "1mo"),
        ("2 months", "2mo"),
        ("1 week", "1w"),
        ("3 weeks", "3w"),
        ("3weeks", "3w"),
        ("1 years", "1y"),
        ("2 years", "2y"),
        ("2 quarters", "2q"),
    ],
)
def test_mandelbrot_channel_queryparams(input_window, expected_window):
    """Test Custom `@field_validator()` on `window` field."""
    params = MandelbrotChannelQueryParams(window=input_window)
    assert params.window == expected_window


@pytest.fixture()
def mandelbrot_channel_data():
    return pl.LazyFrame(
        {
            "date": pl.date_range(
                start=datetime.date(2021, 1, 1),
                end=datetime.date(2021, 1, 3),
                eager=True,
            ),
            "symbol": ["AAPL", "AAPL", "AAPL"],
            "bottom_price": [100.0, 100.0, 100.0],
            "recent_price": [110.0, 110.0, 110.0],
            "top_price": [120.0, 120.0, 120.0],
        }
    )


def test_mandelbrot_channel_data_validation(mandelbrot_channel_data):
    MandelbrotChannelData(mandelbrot_channel_data)


def test_mandelbrot_channel_fetcher():
    """Test the integration of MandelbrotChannelFetcher with actual data fetching."""
    fetcher = MandelbrotChannelFetcher(
        context_params=ToolboxQueryParams(symbol="AMD"),
        command_params=None,
    )
    data = fetcher.fetch_data()
    assert not data.is_empty()
    assert "date" in data.columns
    assert "symbol" in data.columns
    assert "bottom_price" in data.columns
    assert "recent_price" in data.columns
    assert "top_price" in data.columns


def test_mandelbrot_channel_fetcher_integration():
    """Test the MandelbrotChannelFetcher and validate the data with MandelbrotChannelData."""
    fetcher = MandelbrotChannelFetcher(
        context_params=ToolboxQueryParams(symbol="AMD"),
        command_params=None,
    )
    data = fetcher.fetch_data()
    assert not data.is_empty()

    MandelbrotChannelData(data)
