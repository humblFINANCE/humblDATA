from typing import List

import plotly
import plotly.graph_objs as go
import polars as pl

from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.utils import plotly_theme  # noqa: F401


def create_historical_plot(data: pl.DataFrame, symbol: str) -> go.Figure:
    """
    Create a plot for historical data for a given symbol.
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
    )
    return fig


def create_current_plot(data, raw_data, symbol: str) -> go.Figure:
    """
    Create a plot for current data for a given symbol.
    """
    filtered_data = data.filter(pl.col("symbol") == symbol)
    raw_data = raw_data.filter(pl.col("symbol") == symbol)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=raw_data.select("date").to_series(),
            y=raw_data.select("close").to_series(),
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
    )
    return fig


def is_historical_data(data) -> bool:
    """
    Determine if the dataframe contains historical data.
    """
    return data.select("date").to_series().unique().shape[0] > 1


def generate_plot_for_symbol(
    data: pl.DataFrame, raw_data: pl.DataFrame, symbol: str
) -> go.Figure:
    """
    Generate the appropriate plot for a symbol based on the data type.
    """
    if is_historical_data(data):
        return create_historical_plot(data, symbol)
    else:
        return create_current_plot(data, raw_data, symbol)


def generate_plots(data: HumblObject) -> list[go.Figure]:
    """
    Generate a list of plots for each symbol in the dataframe.
    """
    calc_data: pl.DataFrame = data.to_polars()
    raw_data: pl.DataFrame = data.to_polars(raw_data=True)
    symbols = calc_data.select("symbol").unique().to_series()

    plots = [
        generate_plot_for_symbol(calc_data, raw_data, symbol)
        for symbol in symbols
    ]
    return plots
