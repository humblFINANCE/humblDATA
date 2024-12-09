"""
**Context: Toolbox || Category: Technical || Command: momentum**.

The Momentum View Module.
"""

from typing import List

import plotly.graph_objs as go
import polars as pl

from humbldata.core.standard_models.abstract.chart import Chart, ChartTemplate


def create_shifted_plot(
    data: pl.DataFrame,
    equity_data: pl.DataFrame,
    symbol: str,
    template: ChartTemplate = ChartTemplate.plotly,
) -> go.Figure:
    """
    Generate a shifted momentum plot for a given symbol.

    Parameters
    ----------
    data : pl.DataFrame
        The dataframe containing shifted prices and momentum signals
    equity_data : pl.DataFrame
        The dataframe containing historical price data
    symbol : str
        The symbol for which to generate the plot
    template : ChartTemplate
        The template to be used for styling the plot

    Returns
    -------
    go.Figure
        A plotly figure object representing the shifted momentum data
    """
    # Filter data for the specific symbol
    filtered_data = data.filter(pl.col("symbol") == symbol)

    fig = go.Figure()

    # Get dates, prices and shifted prices
    dates = filtered_data.select("date").to_series()
    prices = filtered_data.select("close").to_series()
    shifted_prices = filtered_data.select("shifted").to_series()

    # Create color array based on price comparison
    colors = [
        "green" if p > s else "red" for p, s in zip(prices, shifted_prices)
    ]

    # Add current price trace with color segments
    for i in range(1, len(dates)):
        fig.add_trace(
            go.Scatter(
                x=dates[i - 1 : i + 1],
                y=prices[i - 1 : i + 1],
                mode="lines",
                line=dict(color=colors[i - 1], width=2),
                name="Current Price",
                showlegend=True if i == 1 else False,
            )
        )

    # Add shifted price trace
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=shifted_prices,
            name="Shifted Price",
            line=dict(color="purple", width=2),
        )
    )

    fig.update_layout(
        title=f"Momentum Shift Analysis for {symbol}",
        xaxis_title="Date",
        yaxis_title="Price",
        template=template,
    )

    return fig


def generate_plot_for_symbol(
    data: pl.DataFrame,
    equity_data: pl.DataFrame,
    symbol: str,
    method: str = "shift",
    template: ChartTemplate = ChartTemplate.plotly,
) -> Chart:
    """
    Generate a plot for a specific symbol based on the momentum method used.

    Parameters
    ----------
    data : pl.DataFrame
        The dataframe containing momentum data
    equity_data : pl.DataFrame
        The dataframe containing historical price data
    symbol : str
        The symbol for which to generate the plot
    method : str
        The momentum calculation method used ("shift", "log", or "simple")
    template : ChartTemplate
        The template to use for the plotly figure

    Returns
    -------
    Chart
        A Chart object containing the generated plot
    """
    if method == "shift":
        fig = create_shifted_plot(data, equity_data, symbol, template)
    else:
        # Placeholder for future momentum plot types
        raise NotImplementedError(
            f"Plot generation for method '{method}' not yet implemented"
        )

    return Chart(content=fig.to_json(), fig=fig)


def generate_plots(
    data: pl.LazyFrame,
    equity_data: pl.LazyFrame,
    method: str = "shift",
    template: ChartTemplate = ChartTemplate.plotly,
) -> list[Chart]:
    """
    Generate plots for each unique symbol in the dataset.

    Parameters
    ----------
    data : pl.LazyFrame
        The LazyFrame containing momentum data
    equity_data : pl.LazyFrame
        The LazyFrame containing historical price data
    method : str
        The momentum calculation method used
    template : ChartTemplate
        The template to use for the plotly figures

    Returns
    -------
    List[Chart]
        A list of Chart objects, each containing a plot for a unique symbol
    """
    # Collect the LazyFrames
    collected_data = data.collect()
    collected_equity = equity_data.collect()

    # Get unique symbols
    symbols = collected_data.select("symbol").unique().to_series()

    # Generate plots for each symbol
    plots = [
        generate_plot_for_symbol(
            collected_data, collected_equity, symbol, method, template
        )
        for symbol in symbols
    ]

    return plots
