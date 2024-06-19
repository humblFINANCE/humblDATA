from typing import List

import plotly
import plotly.graph_objs as go
import polars as pl

from humbldata.core.standard_models.abstract.chart import Chart, ChartTemplate
from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.utils import plotly_theme  # noqa: F401


def create_historical_plot(
    data: pl.DataFrame,
    symbol: str,
    template: ChartTemplate = ChartTemplate.plotly,
) -> go.Figure:
    """
    Generate a historical plot for a given symbol from the provided data.

    Parameters
    ----------
    data : pl.DataFrame
        The dataframe containing historical data including dates, bottom prices, close prices, and top prices.
    symbol : str
        The symbol for which the historical plot is to be generated.
    template : ChartTemplate
        The template to be used for styling the plot.

    Returns
    -------
    go.Figure
        A plotly figure object representing the historical data of the given symbol.
    """
    filtered_data = data.filter(pl.col("symbol") == symbol)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=filtered_data.select("date").to_series(),
            y=filtered_data.select("bottom_price").to_series(),
            name="Bottom Price",
            line=dict(color="green"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=filtered_data.select("date").to_series(),
            y=filtered_data.select("close_price").to_series(),
            name="Recent Price",
            line=dict(color="blue"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=filtered_data.select("date").to_series(),
            y=filtered_data.select("top_price").to_series(),
            name="Top Price",
            line=dict(color="red"),
        )
    )
    fig.update_layout(
        title=f"Historical Mandelbrot Channel for {symbol}",
        xaxis_title="Date",
        yaxis_title="Price",
        template=template,
    )
    return fig


def create_current_plot(
    data: pl.DataFrame,
    equity_data: pl.DataFrame,
    symbol: str,
    template: ChartTemplate = ChartTemplate.plotly,
) -> go.Figure:
    """
    Generate a current plot for a given symbol from the provided data and equity data.

    Parameters
    ----------
    data : pl.DataFrame
        The dataframe containing historical data including top and bottom prices.
    equity_data : pl.DataFrame
        The dataframe containing current equity data including dates and close prices.
    symbol : str
        The symbol for which the current plot is to be generated.
    template : ChartTemplate
        The template to be used for styling the plot.

    Returns
    -------
    go.Figure
        A plotly figure object representing the current data of the given symbol.
    """
    filtered_data = data.filter(pl.col("symbol") == symbol)
    equity_data = equity_data.filter(pl.col("symbol") == symbol)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=equity_data.select("date").to_series(),
            y=equity_data.select("close").to_series(),
            name="Recent Price",
            line=dict(color="blue"),
        )
    )
    fig.add_hline(
        y=filtered_data.select("top_price").row(0)[0],
        line=dict(color="red", width=2),
        name="Top Price",
    )
    fig.add_hline(
        y=filtered_data.select("bottom_price").row(0)[0],
        line=dict(color="green", width=2),
        name="Bottom Price",
    )
    fig.update_layout(
        title=f"Current Mandelbrot Channel for {symbol}",
        xaxis_title="Date",
        yaxis_title="Price",
        template=template,
    )
    return fig


def is_historical_data(data: pl.DataFrame) -> bool:
    """
    Check if the provided dataframe contains historical data based on the uniqueness of dates.

    Parameters
    ----------
    data : pl.DataFrame
        The dataframe to check for historical data presence.

    Returns
    -------
    bool
        Returns True if the dataframe contains historical data (more than one unique date), otherwise False.
    """
    return data.select("date").to_series().unique().shape[0] > 1


def generate_plot_for_symbol(
    data: pl.DataFrame,
    equity_data: pl.DataFrame,
    symbol: str,
    template: ChartTemplate = ChartTemplate.plotly,
) -> Chart:
    """
    Generate a plot for a specific symbol that is filtered from the original DF.

    This function will check if the data provided is a Historical or Current
    Mandelbrot Channel data. If it is historical, it will generate a historical
    plot. If it is current, it will generate a current plot.

    Parameters
    ----------
    data : pl.DataFrame
        The dataframe containing Mandelbrot channel data for all symbols.
    equity_data : pl.DataFrame
        The dataframe containing equity data for all symbols.
    symbol : str
        The symbol for which to generate the plot.
    template : ChartTemplate
        The template/theme to use for the plotly figure. Options are:
        "humbl_light", "humbl_dark", "plotly_light", "plotly_dark", "ggplot2", "seaborn", "simple_white", "none"

    Returns
    -------
    Chart
        A Chart object containing the generated plot for the specified symbol.

    """
    if is_historical_data(data):
        out = create_historical_plot(data, symbol, template)
    else:
        out = create_current_plot(data, equity_data, symbol, template)

    return Chart(content=out.to_plotly_json(), fig=out)


def generate_plots(
    data: pl.LazyFrame,
    equity_data: pl.LazyFrame,
    template: ChartTemplate = ChartTemplate.plotly,
) -> list[Chart]:
    """
    Context: Toolbox || Category: Technical || Subcategory: Mandelbrot Channel || **Command: generate_plots()**.

    Generate plots for each unique symbol in the given dataframes.

    Parameters
    ----------
    data : pl.LazyFrame
        The LazyFrame containing the symbols and MandelbrotChannelData
    equity_data : pl.LazyFrame
        The LazyFrame containing equity data for the symbols.
    template : ChartTemplate
        The template/theme to use for the plotly figure.

    Returns
    -------
    list[Chart]
        A list of Chart objects, each representing a plot for a unique symbol.

    """
    symbols = data.select("symbol").unique().collect().to_series()

    plots = [
        generate_plot_for_symbol(
            data.collect(), equity_data.collect(), symbol, template
        )
        for symbol in symbols
    ]
    return plots
