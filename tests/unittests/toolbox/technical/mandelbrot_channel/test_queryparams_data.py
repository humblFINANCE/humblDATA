import datetime

import polars as pl
import pytest

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
