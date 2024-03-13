import polars as pl
import pytest
from _pytest.fixtures import FixtureRequest

from humbldata.toolbox.technical.mandelbrot_channel.model import (
    calc_mandelbrot_channel,
)


# FIXTURES =====================================================================
@pytest.fixture(
    params=[
        "dataframe_single_symbol",
        "lazyframe_single_symbol",
        "dataframe_multiple_symbols",
        "lazyframe_multiple_symbols",
    ]
)
def equity_historical(request: FixtureRequest):
    """One year of equity data, AAPL & AMZN symbols."""
    data = pl.read_csv(
        "tests\\toolbox\\custom_data\\equity_historical_multiple_1y.csv",
        try_parse_dates=True,
    )
    if request.param == "dataframe_single_symbol":
        data = data.filter(pl.col("symbol") == "AAPL")
        return data
    elif request.param == "lazyframe_single_symbol":
        data = data.filter(pl.col("symbol") == "AAPL")
        return pl.LazyFrame(data)
    elif request.param == "dataframe_multiple_symbols":
        return data
    elif request.param == "lazyframe_multiple_symbols":
        return pl.LazyFrame(data)
    return None


@pytest.mark.integration()
def test_mandelbrot_channel_integration(equity_historical):
    """Testing the composed function of `calc_mandelbrot_channel()`."""
    mandelbrot = calc_mandelbrot_channel(
        equity_historical,
        window="1m",
        rv_adjustment=True,
        _rv_method="std",
        _rv_grouped_mean=False,
        _rs_method="RS",
        _live_price=False,
    ).collect()
