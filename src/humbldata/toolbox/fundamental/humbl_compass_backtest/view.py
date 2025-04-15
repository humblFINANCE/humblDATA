import plotly.graph_objs as go
import polars as pl

from humbldata.core.standard_models.abstract.chart import Chart, ChartTemplate
from humbldata.core.utils import plotly_theme  # noqa: F401


def create_backtest_plot(
    equity_data: pl.LazyFrame,
    regime_date_summary: pl.LazyFrame,
    symbol: str = "",
    template: ChartTemplate = ChartTemplate.plotly,
) -> go.Figure:
    """
    Generate a backtest plot with equity data and regime overlay shading.

    Parameters
    ----------
    equity_data : pl.LazyFrame
        The LazyFrame containing date and close price data.
    regime_date_summary : pl.LazyFrame
        The LazyFrame containing regime data with humbl_regime, regime_instance_id,
        start_date, and end_date columns.
    symbol : str, optional
        The symbol for which the backtest plot is to be generated.
    template : ChartTemplate, optional
        The template to be used for styling the plot.

    Returns
    -------
    go.Figure
        A plotly figure object representing the backtest data with regime shading.
    """
    # Collect data from LazyFrames
    equity_df = equity_data.collect()
    regime_df = regime_date_summary.collect()

    # Create the figure
    fig = go.Figure()

    # Add equity price trace
    fig.add_trace(
        go.Scatter(
            x=equity_df.select("date").to_series(),
            y=equity_df.select("close").to_series(),
            name="Price",
            line=dict(color="black", width=2),
        )
    )

    # Define colors for each regime
    regime_colors = {
        "humblBOOM": "rgba(0, 255, 0, 0.4)",  # Green with transparency
        "humblBOUNCE": "rgba(0, 0, 255, 0.4)",  # Blue with transparency
        "humblBLOAT": "rgba(255, 165, 0, 0.4)",  # Orange with transparency
        "humblBUST": "rgba(255, 0, 0, 0.4)",  # Red with transparency
    }

    # Add shaded regions for each regime period
    for row in regime_df.iter_rows(named=True):
        regime = row["humbl_regime"]
        start_date = row["start_date"]
        end_date = row["end_date"]
        color = regime_colors.get(
            regime, "rgba(128, 128, 128, 0.2)"
        )  # Default gray if regime not found

        # Add a vertical rectangle for each regime period
        fig.add_vrect(
            x0=start_date,
            x1=end_date,
            fillcolor=color,
            opacity=1,
            layer="below",
            line_width=0,
        )

    # Update layout
    title = (
        f"Humbl Compass Backtest for {symbol}"
        if symbol
        else "Humbl Compass Backtest"
    )
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price",
        template=template,
        legend_title="Legend",
    )

    return fig


def generate_plot_for_symbol(
    equity_data: pl.LazyFrame,
    regime_date_summary: pl.LazyFrame,
    symbol: str,
    template: ChartTemplate = ChartTemplate.plotly,
) -> Chart:
    """
    Generate a backtest plot for a specific symbol.

    Parameters
    ----------
    equity_data : pl.LazyFrame
        The LazyFrame containing equity data for all symbols.
    regime_date_summary : pl.LazyFrame
        The LazyFrame containing regime data for all symbols.
    symbol : str
        The symbol for which to generate the plot.
    template : ChartTemplate, optional
        The template to be used for styling the plot.

    Returns
    -------
    Chart
        A Chart object containing the generated backtest plot for the specified symbol.
    """
    # Filter data for the specific symbol
    filtered_equity_data = equity_data.filter(pl.col("symbol") == symbol)
    filtered_regime_data = regime_date_summary.filter(
        pl.col("symbol") == symbol
    )

    # Create the plot
    fig = create_backtest_plot(
        filtered_equity_data, filtered_regime_data, symbol, template
    )

    return Chart(content=fig.to_json(), fig=fig)


def generate_plots(
    equity_data: pl.LazyFrame,
    regime_date_summary: pl.LazyFrame,
    template: ChartTemplate = ChartTemplate.plotly,
) -> list[Chart]:
    """
    Context: Toolbox || Category: Fundamental || Subcategory: Humbl Compass Backtest || **Command: generate_plots()**.

    Generate backtest plots for each unique symbol in the given dataframes.

    Parameters
    ----------
    equity_data : pl.LazyFrame
        The LazyFrame containing equity data for all symbols.
    regime_date_summary : pl.LazyFrame
        The LazyFrame containing regime data for all symbols.
    template : ChartTemplate, optional
        The template to be used for styling the plots.

    Returns
    -------
    list[Chart]
        A list of Chart objects, each representing a plot for a unique symbol.
    """
    # Get unique symbols
    symbols = equity_data.select("symbol").unique().collect().to_series()

    # Generate plots for each symbol
    plots = [
        generate_plot_for_symbol(
            equity_data, regime_date_summary, symbol, template
        )
        for symbol in symbols
    ]

    return plots
