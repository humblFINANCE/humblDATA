import polars as pl
import pytest
from _pytest.fixtures import FixtureRequest
from plotly.graph_objs import Figure

from humbldata.core.standard_models.abstract.chart import Chart
from humbldata.toolbox.technical.humbl_channel.view import (
    generate_plot_for_symbol,
    generate_plots,
)


@pytest.fixture(params=["historical", "current"])
def mandelbrot_data(request):
    """HumblChannelData Output from `.mandelbrot()`."""
    data_historical = pl.read_parquet(
        "tests/test_data/humbl_channel_historical.parquet"
    )
    if request.param == "current":
        out = data_historical.group_by("symbol").agg(pl.col("*").last())
    elif request.param == "historical":
        out = data_historical
    return out


@pytest.fixture()
def equity_data(mandelbrot_data):
    return mandelbrot_data.select("close_price", "date", "symbol").rename(
        {"close_price": "close"}
    )


def test_generate_plot_for_symbol(
    mandelbrot_data, equity_data, request: FixtureRequest
):
    """Test to check if routing the plot function is correctly generated."""
    current_param = request.node.callspec.params.get("mandelbrot_data")

    if current_param == "historical":
        plots = generate_plot_for_symbol(
            mandelbrot_data, equity_data, symbol="AAPL"
        )
        assert isinstance(plots.content, dict)
        assert isinstance(plots.fig, Figure)
        assert isinstance(plots, Chart)
    if current_param == "current":
        plots = generate_plot_for_symbol(
            mandelbrot_data, equity_data, symbol="AAPL"
        )
        assert isinstance(plots.content, dict)
        assert isinstance(plots.fig, Figure)
        assert isinstance(plots, Chart)


def test_generate_plots(mandelbrot_data, equity_data, request: FixtureRequest):
    """Test to check if routing the plot function is correctly generated."""
    current_param = request.node.callspec.params.get("mandelbrot_data")

    plots = generate_plots(mandelbrot_data.lazy(), equity_data.lazy())

    assert isinstance(plots, list)
    assert len(plots) == 5
    for plot in plots:
        plot_title = plot.content.get("layout").get("title").get("text")
        assert f"{current_param.capitalize()} Mandelbrot Channel" in plot_title
        assert isinstance(plot, Chart)
        assert isinstance(plot.content, dict)
        assert isinstance(plot.fig, Figure)
        assert plot.content.get("data") is not None
        assert plot.content.get("layout") is not None
