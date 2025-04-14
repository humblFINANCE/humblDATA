"""
**Context: Toolbox || Category: Technical || Command: momentum**.

The Momentum View Module.

# TODO: Add plotting logic to just use momentum_signal column.
"""

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
        "green" if p > s else "red"
        for p, s in zip(prices, shifted_prices, strict=False)
    ]

    # Add current price trace with color segments
    for i in range(1, len(dates)):
        fig.add_trace(
            go.Scatter(
                x=dates[i - 1 : i + 1],
                y=prices[i - 1 : i + 1],
                mode="lines",
                line={"color": colors[i - 1], "width": 2},
                name="Current Price",
                showlegend=i == 1,
            )
        )

    # Add shifted price trace
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=shifted_prices,
            name="Shifted Price",
            line={"color": "purple", "width": 2},
        )
    )

    fig.update_layout(
        title=f"Momentum Shift Analysis for {symbol}",
        xaxis_title="Date",
        yaxis_title="Price",
        template=template,
    )

    return fig


def create_simple_plot(
    data: pl.DataFrame,
    equity_data: pl.DataFrame,
    symbol: str,
    template: ChartTemplate = ChartTemplate.plotly,
    overlay: bool = False,
) -> go.Figure:
    """
    Generate a simple momentum plot with price and momentum indicator.

    Parameters
    ----------
    data : pl.DataFrame
        The dataframe containing momentum data
    equity_data : pl.DataFrame
        The dataframe containing historical price data
    symbol : str
        The symbol for which to generate the plot
    template : ChartTemplate
        The template to be used for styling the plot
    overlay : bool, default False
        If True, shows momentum overlaid on price.
        If False, shows price colored by momentum value.

    Returns
    -------
    go.Figure
        A plotly figure object representing price and momentum data
    """
    # Filter data for the specific symbol
    filtered_data = data.filter(pl.col("symbol") == symbol)

    # Create figure
    fig = go.Figure()

    # Get dates, prices and momentum values
    dates = filtered_data.select("date").to_series()
    prices = filtered_data.select("close").to_series()
    momentum = filtered_data.select("momentum").to_series()

    if overlay:
        # Add price trace on primary y-axis (left)
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=prices,
                name="Price",
                line={"color": "blue", "width": 2},
                yaxis="y1",
            )
        )

        # Add momentum trace on secondary y-axis (right)
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=momentum,
                name="Momentum",
                line={"color": "purple", "width": 2},
                yaxis="y2",
            )
        )

        # Update layout with separate y-axes
        fig.update_layout(
            title=f"Price and Momentum Analysis for {symbol}",
            xaxis={"title": "Date"},
            # Primary y-axis (Price) on the left
            yaxis={
                "title": "Price",
                "titlefont": {"color": "blue"},
                "tickfont": {"color": "blue"},
                "side": "left",
            },
            # Secondary y-axis (Momentum) on the right
            yaxis2={
                "title": "Momentum",
                "titlefont": {"color": "purple"},
                "tickfont": {"color": "purple"},
                "side": "right",
                "overlaying": "y",
            },
            template=template,
            showlegend=True,
            legend={
                "x": 0.45,
                "y": 1.15,
                "xanchor": "center",
                "orientation": "h",
            },
        )
    else:
        # Create color array based on momentum values
        colors = ["green" if m > 0 else "red" for m in momentum]

        # Add price trace with color segments
        for i in range(1, len(dates)):
            fig.add_trace(
                go.Scatter(
                    x=dates[i - 1 : i + 1],
                    y=prices[i - 1 : i + 1],
                    mode="lines",
                    line=dict(color=colors[i - 1], width=2),
                    name="Price",
                    showlegend=True if i == 1 else False,
                )
            )

        # Update layout for single axis
        fig.update_layout(
            title=f"Price Colored by Momentum for {symbol}",
            xaxis_title="Date",
            yaxis_title="Price",
            template=template,
            showlegend=True,
            legend=dict(
                x=0.45,
                y=1.15,
                xanchor="center",
                orientation="h",
            ),
        )

    return fig


def generate_plot_for_symbol(
    data: pl.DataFrame,
    equity_data: pl.DataFrame,
    symbol: str,
    method: str = "shift",
    template: ChartTemplate = ChartTemplate.plotly,
    overlay: bool = False,
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
    overlay : bool, default False
        If True, shows momentum overlaid on price.
        If False, shows price colored by momentum value.

    Returns
    -------
    Chart
        A Chart object containing the generated plot
    """
    if method == "shift":
        fig = create_shifted_plot(data, equity_data, symbol, template)
    elif method in ["simple", "log"]:
        fig = create_simple_plot(data, equity_data, symbol, template, overlay)
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
    overlay: bool = False,
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
    overlay : bool, default False
        If True, shows momentum overlaid on price.
        If False, shows price colored by momentum value.

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
            collected_data,
            collected_equity,
            symbol,
            method,
            template,
            overlay,
        )
        for symbol in symbols
    ]

    return plots
