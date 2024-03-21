import polars as pl
import pytest
from _pytest.fixtures import FixtureRequest
from plotly.graph_objs import Figure

from humbldata.toolbox.technical.mandelbrot_channel.view import (
    create_current_plot,
    create_historical_plot,
)


@pytest.fixture(params=["historical", "current"])
def mandelbrot_data(request):
    data_historical = pl.read_csv(
        "tests\\unittests\\toolbox\\custom_data\\mandelbrot_channel_historical_data_multiple_4y.csv"
    )
    if request.param == "current":
        out = data_historical.group_by("symbol").agg(pl.col("*").last())
    elif request.param == "historical":
        out = data_historical
    return out


def test_create_historical_plot(mandelbrot_data, request: FixtureRequest):
    current_param = request.node.callspec.params.get("mandelbrot_data")

    if current_param == "historical":
        plots = create_historical_plot(mandelbrot_data, symbol="AAPL")
        assert isinstance(plots, Figure)
