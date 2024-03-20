from typing import List

import plotly
import plotly.graph_objs as go
import polars as pl

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


def create_current_plot(data, symbol: str) -> go.Figure:
    """
    Create a plot for current data for a given symbol.
    """
    filtered_data = data.filter(pl.col("symbol") == symbol)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=filtered_data.select("date").to_series(),
            y=filtered_data.select("recent_price").to_series(),
            name="Recent Price",
            line=dict(color="blue"),
        )
    )
    fig.add_hline(
        y=filtered_data.select("top_price").max(),
        line=dict(color="red", width=2),
        name="Top Price",
    )
    fig.add_hline(
        y=filtered_data.select("bottom_price").min(),
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


def generate_plot_for_symbol(data: pl.DataFrame, symbol: str) -> go.Figure:
    """
    Generate the appropriate plot for a symbol based on the data type.
    """
    if is_historical_data(data):
        return create_historical_plot(data, symbol)
    else:
        return create_current_plot(data, symbol)


def generate_plots(data: pl.DataFrame) -> list[go.Figure]:
    """
    Generate a list of plots for each symbol in the dataframe.
    """
    symbols = data.select("symbol").unique().to_series()
    plots = [generate_plot_for_symbol(data, symbol) for symbol in symbols]
    return plots
