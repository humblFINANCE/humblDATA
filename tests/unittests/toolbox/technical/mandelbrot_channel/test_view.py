import polars as pl
import pytest
from _pytest.fixtures import FixtureRequest
from plotly.graph_objs import Figure

from humbldata.toolbox.technical.mandelbrot_channel.view import (
    create_current_plot,
    create_historical_plot,
    is_historical_data,
)


@pytest.fixture(params=["historical", "current"])
def mandelbrot_data(request):
    """MandelbrotChannelData Output from `.mandelbrot()`."""
    data_historical = pl.read_parquet("tests/test_data/test_data.parquet")
    if request.param == "current":
        out = data_historical.group_by("symbol").agg(pl.col("*").last())
    elif request.param == "historical":
        out = data_historical
    return out


def test_create_historical_plot(mandelbrot_data, request: FixtureRequest):
    """Test to check if historical plot is created."""
    current_param = request.node.callspec.params.get("mandelbrot_data")

    if current_param == "historical":
        plots = create_historical_plot(mandelbrot_data, symbol="AAPL")
        assert isinstance(plots, Figure)


def test_create_current_plot(mandelbrot_data, request: FixtureRequest):
    """Test to check if current plot is created."""
    current_param = request.node.callspec.params.get("mandelbrot_data")

    if current_param == "current":
        equity_data = mandelbrot_data.select(
            "close_price", "date", "symbol"
        ).rename({"close_price": "close"})

        plots = create_current_plot(mandelbrot_data, equity_data, symbol="AAPL")
        assert isinstance(plots, Figure)


def test_is_historical_data(mandelbrot_data, request: FixtureRequest):
    """Test to check if mandelbrot data is historical or current."""
    current_param = request.node.callspec.params.get("mandelbrot_data")

    if current_param == "historical":
        assert is_historical_data(mandelbrot_data) is True
    if current_param == "current":
        assert is_historical_data(mandelbrot_data) is False
