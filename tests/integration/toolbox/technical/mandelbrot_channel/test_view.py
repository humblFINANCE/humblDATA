import polars as pl
import pytest
from _pytest.fixtures import FixtureRequest
from plotly.graph_objs import Figure

from humbldata.core.standard_models.abstract.chart import Chart
from humbldata.toolbox.technical.mandelbrot_channel.view import (
    generate_plot_for_symbol,
    generate_plots,
)


@pytest.fixture(params=["historical", "current"])
def mandelbrot_data(request):
    """MandelbrotChannelData Output from `.mandelbrot()`."""
    data_historical = pl.read_csv(
        "tests\\unittests\\toolbox\\custom_data\\mandelbrot_channel_historical_data_multiple_4y.csv"
    )
    if request.param == "current":
        out = data_historical.group_by("symbol").agg(pl.col("*").last())
    elif request.param == "historical":
        out = data_historical
    return out


def test_generate_plot_for_symbol(mandelbrot_data, request: FixtureRequest):
    """Test to check if routing the plot function is correctly generated."""
    current_param = request.node.callspec.params.get("mandelbrot_data")

    equity_data = mandelbrot_data.select(
        "close_price", "date", "symbol"
    ).rename({"close_price": "close"})

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


def test_generate_plots(mandelbrot_data, request: FixtureRequest):
    """Test to check if routing the plot function is correctly generated."""
    current_param = request.node.callspec.params.get("mandelbrot_data")

    equity_data = mandelbrot_data.select(
        "close_price", "date", "symbol"
    ).rename({"close_price": "close"})

    if current_param == "historical":
        plots = generate_plots(mandelbrot_data.lazy(), equity_data.lazy())

        assert isinstance(plots, list)
        assert len(plots) == 2
        for plot in plots:
            plot_title = plot.content.get("layout").get("title").get("text")

            assert "Historical Mandelbrot Channel" in plot_title
            assert isinstance(plot, Chart)
            assert isinstance(plot.content, dict)
            assert isinstance(plot.fig, Figure)

    if current_param == "current":
        plots = generate_plots(mandelbrot_data.lazy(), equity_data.lazy())

        assert isinstance(plots, list)
        assert len(plots) == 2
        for plot in plots:
            plot_title = plot.content.get("layout").get("title").get("text")

            assert "Current Mandelbrot Channel" in plot_title
            assert isinstance(plot, Chart)
            assert isinstance(plot.content, dict)
            assert isinstance(plot.fig, Figure)
