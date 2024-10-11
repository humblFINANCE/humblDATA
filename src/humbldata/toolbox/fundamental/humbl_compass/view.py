"""
**Context: Toolbox || Category: Fundamental || Command: humbl_compass**.

The HumblCompass View Module.
"""

from typing import List

import plotly.graph_objs as go
import polars as pl
from plotly.colors import sequential

from humbldata.core.standard_models.abstract.chart import Chart, ChartTemplate


def create_humbl_compass_plot(
    data: pl.DataFrame,
    template: ChartTemplate = ChartTemplate.plotly,
) -> go.Figure:
    """
    Generate a HumblCompass plot from the provided data.

    Parameters
    ----------
    data : pl.DataFrame
        The dataframe containing the data to be plotted.
    template : ChartTemplate
        The template to be used for styling the plot.

    Returns
    -------
    go.Figure
        A plotly figure object representing the HumblCompass plot.
    """
    # Sort data by date and create a color scale
    data = data.sort("date_month_start")
    color_scale = sequential.deep

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data["cpi_3m_delta"],
            y=data["cli_3m_delta"],
            mode="lines+markers+text",
            name="HumblCompass Data",
            text=data["date_month_start"].dt.strftime("%b %Y"),
            textposition="top center",
            textfont=dict(size=10),
            marker=dict(
                size=10,
                color=list(range(len(data))),  # Use index for color mapping
                colorscale=color_scale,
                colorbar=dict(title="Time"),
            ),
            line=dict(
                color="rgba(0,0,0,0.5)"
            ),  # Single color for lines with some transparency
            hovertemplate="<b>%{text}</b><br>CPI 3m Δ: %{x:.2f}<br>CLI 3m Δ: %{y:.2f}<extra></extra>",
        )
    )

    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.7)
    fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.7)

    fig.update_layout(
        title="humblCOMPASS: CLI 3m Delta vs CPI 3m Delta",
        xaxis_title="CPI 3-Month Delta",
        yaxis_title="CLI 3-Month Delta",
        template=template,
        hovermode="closest",
    )

    # Update colorbar ticks to show actual dates
    fig.update_coloraxes(
        colorbar=dict(
            tickvals=[0, len(data) - 1],
            ticktext=[
                data["date_month_start"].min().strftime("%b %Y"),
                data["date_month_start"].max().strftime("%b %Y"),
            ],
        )
    )

    return fig


def generate_plots(
    data: pl.LazyFrame,
    template: ChartTemplate = ChartTemplate.plotly,
) -> List[Chart]:
    """
    Context: Toolbox || Category: Fundamental || Command: humbl_compass || **Function: generate_plots()**.

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
    plot = create_humbl_compass_plot(collected_data, template)
    return [Chart(content=plot.to_json(), fig=plot)]
