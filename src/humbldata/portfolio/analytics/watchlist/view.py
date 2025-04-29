"""
**Context: Portfolio || Category: Analytics || Command: watchlist_table**.

The Watchlist Table View Module.
"""

from typing import List

import plotly.graph_objs as go
import polars as pl

from humbldata.core.standard_models.abstract.chart import Chart, ChartTemplate


def create_example_plot(
    data: pl.DataFrame,
    template: ChartTemplate = ChartTemplate.plotly,
) -> go.Figure:
    """
    Generate an example plot from the provided data.

    Parameters
    ----------
    data : pl.DataFrame
        The dataframe containing the data to be plotted.
    template : ChartTemplate
        The template to be used for styling the plot.

    Returns
    -------
    go.Figure
        A plotly figure object representing the example plot.
    """
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data.select("x_column").to_series(),
            y=data.select("y_column").to_series(),
            name="Example Data",
            line=dict(color="blue"),
        )
    )
    fig.update_layout(
        title="Example Plot",
        xaxis_title="X Axis",
        yaxis_title="Y Axis",
        template=template,
    )
    return fig


def generate_plots(
    data: pl.LazyFrame,
    template: ChartTemplate = ChartTemplate.plotly,
) -> List[Chart]:
    """
    Context: Portfolio || Category: Analytics || Command: watchlist_table || **Function: generate_plots()**.

    Generate plots from the given dataframe.

    Parameters
    ----------
    data : pl.LazyFrame
        The LazyFrame containing the data to be plotted.
    template : ChartTemplate
        The template/theme to use for the plotly figure.

    Returns
    -------
    List[Chart]
        A list of Chart objects, each representing a plot.
    """
    collected_data = data.collect()
    plot = create_example_plot(collected_data, template)
    return [Chart(content=plot.to_plotly_json(), fig=plot)]
