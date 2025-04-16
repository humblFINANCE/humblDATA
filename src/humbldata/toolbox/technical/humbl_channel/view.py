import plotly
import plotly.graph_objs as go
import polars as pl

from humbldata.core.standard_models.abstract.chart import Chart, ChartTemplate
from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.utils import plotly_theme  # noqa: F401

# Color constants for easy modification
MOMENTUM_COLORS = {
    "positive": "blue",
    "negative": "yellow",
    "default": "blue",  # Used when no momentum data
}

CHANNEL_COLORS = {
    "top": "red",
    "bottom": "green",
}


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

    # Check if momentum_signal exists
    has_momentum = "momentum_signal" in filtered_data.schema.names()

    if has_momentum:
        # Get all series at once
        dates = filtered_data.select("date").to_series()
        prices = filtered_data.select("recent_price").to_series()
        signals = filtered_data.select("momentum_signal").to_series()

        # Split data into positive and negative momentum
        pos_dates = []
        pos_prices = []
        neg_dates = []
        neg_prices = []

        # Add first point to appropriate list
        if signals[0] == 1:
            pos_dates.append(dates[0])
            pos_prices.append(prices[0])
        else:
            neg_dates.append(dates[0])
            neg_prices.append(prices[0])

        # Process each point
        for i in range(len(signals)):
            if signals[i] == 1:
                pos_dates.append(dates[i])
                pos_prices.append(prices[i])
                # If next point exists and has different momentum, add None for gap
                if i < len(signals) - 1 and signals[i + 1] != 1:
                    pos_dates.append(dates[i + 1])
                    pos_prices.append(prices[i + 1])
                    pos_dates.append(None)
                    pos_prices.append(None)
            else:
                neg_dates.append(dates[i])
                neg_prices.append(prices[i])
                # If next point exists and has different momentum, add None for gap
                if i < len(signals) - 1 and signals[i + 1] != 0:
                    neg_dates.append(dates[i + 1])
                    neg_prices.append(prices[i + 1])
                    neg_dates.append(None)
                    neg_prices.append(None)

        # Add positive momentum trace
        if pos_dates:
            fig.add_trace(
                go.Scatter(
                    x=pos_dates,
                    y=pos_prices,
                    mode="lines",
                    line=dict(color=MOMENTUM_COLORS["positive"], width=2),
                    name="Price (Positive Momentum)",
                )
            )

        # Add negative momentum trace
        if neg_dates:
            fig.add_trace(
                go.Scatter(
                    x=neg_dates,
                    y=neg_prices,
                    mode="lines",
                    line=dict(color=MOMENTUM_COLORS["negative"], width=2),
                    name="Price (Negative Momentum)",
                )
            )
    else:
        # Original price trace if no momentum
        fig.add_trace(
            go.Scatter(
                x=filtered_data.select("date").to_series(),
                y=filtered_data.select("recent_price").to_series(),
                name="Recent Price",
                line=dict(color=MOMENTUM_COLORS["default"]),
            )
        )

    fig.add_trace(
        go.Scatter(
            x=filtered_data.select("date").to_series(),
            y=filtered_data.select("bottom_price").to_series(),
            name="Bottom Price",
            line=dict(color=CHANNEL_COLORS["bottom"]),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=filtered_data.select("date").to_series(),
            y=filtered_data.select("top_price").to_series(),
            name="Top Price",
            line=dict(color=CHANNEL_COLORS["top"]),
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

    # Check if momentum_signal exists
    has_momentum = "momentum_signal" in equity_data.schema.names()

    if has_momentum:
        # Get all series at once
        dates = equity_data.select("date").to_series()
        prices = equity_data.select("close").to_series()
        signals = equity_data.select("momentum_signal").to_series()

        # Split data into positive and negative momentum
        pos_dates = []
        pos_prices = []
        neg_dates = []
        neg_prices = []

        # Add first point to appropriate list
        if signals[0] == 1:
            pos_dates.append(dates[0])
            pos_prices.append(prices[0])
        else:
            neg_dates.append(dates[0])
            neg_prices.append(prices[0])

        # Process each point
        for i in range(len(signals)):
            if signals[i] == 1:
                pos_dates.append(dates[i])
                pos_prices.append(prices[i])
                # If next point exists and has different momentum, add None for gap
                if i < len(signals) - 1 and signals[i + 1] != 1:
                    pos_dates.append(dates[i + 1])
                    pos_prices.append(prices[i + 1])
                    pos_dates.append(None)
                    pos_prices.append(None)
            else:
                neg_dates.append(dates[i])
                neg_prices.append(prices[i])
                # If next point exists and has different momentum, add None for gap
                if i < len(signals) - 1 and signals[i + 1] != 0:
                    neg_dates.append(dates[i + 1])
                    neg_prices.append(prices[i + 1])
                    neg_dates.append(None)
                    neg_prices.append(None)

        # Add positive momentum trace
        if pos_dates:
            fig.add_trace(
                go.Scatter(
                    x=pos_dates,
                    y=pos_prices,
                    mode="lines",
                    line=dict(color=MOMENTUM_COLORS["positive"], width=2),
                    name="Price (Positive Momentum)",
                )
            )

        # Add negative momentum trace
        if neg_dates:
            fig.add_trace(
                go.Scatter(
                    x=neg_dates,
                    y=neg_prices,
                    mode="lines",
                    line=dict(color=MOMENTUM_COLORS["negative"], width=2),
                    name="Price (Negative Momentum)",
                )
            )
    else:
        # Original price trace if no momentum
        fig.add_trace(
            go.Scatter(
                x=equity_data.select("date").to_series(),
                y=equity_data.select("close").to_series(),
                name="Recent Price",
                line=dict(color=MOMENTUM_COLORS["default"]),
            )
        )

    fig.add_hline(
        y=filtered_data.select("top_price").row(0)[0],
        line=dict(color=CHANNEL_COLORS["top"], width=2),
        name="Top Price",
    )
    fig.add_hline(
        y=filtered_data.select("bottom_price").row(0)[0],
        line=dict(color=CHANNEL_COLORS["bottom"], width=2),
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
    momentum_data: pl.DataFrame | None = None,
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
        The template/theme to use for the plotly figure.
    momentum_data : pl.DataFrame | None, optional
        Optional dataframe containing historical momentum signals. If provided,
        will be used to color the equity price trace in current plot mode.

    Returns
    -------
    Chart
        A Chart object containing the generated plot for the specified symbol.
    """
    if is_historical_data(data):
        out = create_historical_plot(data, symbol, template)
    else:
        # If we have momentum data, merge it with equity data
        if momentum_data is not None:
            equity_data = equity_data.join(
                momentum_data.select(["date", "symbol", "momentum_signal"]),
                on=["date", "symbol"],
                how="left",
            )
        out = create_current_plot(data, equity_data, symbol, template)

    return Chart(content=out.to_json(), fig=out)


def generate_plots(
    data: pl.LazyFrame,
    equity_data: pl.LazyFrame,
    template: ChartTemplate = ChartTemplate.plotly,
    momentum_data: pl.LazyFrame | None = None,
) -> list[Chart]:
    """
    Context: Toolbox || Category: Technical || Subcategory: Mandelbrot Channel || **Command: generate_plots()**.

    Generate plots for each unique symbol in the given dataframes.

    Parameters
    ----------
    data : pl.LazyFrame
        The LazyFrame containing the symbols and HumblChannelData
    equity_data : pl.LazyFrame
        The LazyFrame containing equity data for the symbols.
    template : ChartTemplate
        The template/theme to use for the plotly figure.
    momentum_data : pl.LazyFrame | None, optional
        Optional LazyFrame containing historical momentum signals. If provided,
        will be used to color the equity price trace in current plot mode.

    Returns
    -------
    list[Chart]
        A list of Chart objects, each representing a plot for a unique symbol.
    """
    symbols = data.select("symbol").unique().collect().to_series()

    # Collect DataFrames once for efficiency
    data_df = data.collect()
    equity_df = equity_data.collect()
    momentum_df = momentum_data.collect() if momentum_data is not None else None

    plots = [
        generate_plot_for_symbol(
            data_df,
            equity_df,
            symbol,
            template,
            momentum_df,
        )
        for symbol in symbols
    ]
    return plots
