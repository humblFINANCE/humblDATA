"""
**Context: Toolbox || Category: Fundamental || Command: humbl_compass**.

The HumblCompass View Module.
"""

from typing import List

import plotly.graph_objs as go
import polars as pl
from plotly.colors import sequential, sample_colorscale
import datetime

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
    full_color_scale = sequential.Reds
    custom_colorscale = sample_colorscale(full_color_scale, [0.2, 0.8])

    fig = go.Figure()

    # Add colored quadrants from -10 to 10
    quadrants = [
        {
            "x": [0, 10],
            "y": [0, 10],
            "fillcolor": "rgba(173, 216, 230, 0.3)",
        },  # Light blue
        {
            "x": [-10, 0],
            "y": [0, 10],
            "fillcolor": "rgba(144, 238, 144, 0.3)",
        },  # Green
        {
            "x": [0, 10],
            "y": [-10, 0],
            "fillcolor": "rgba(255, 165, 0, 0.3)",
        },  # Orange
        {
            "x": [-10, 0],
            "y": [-10, 0],
            "fillcolor": "rgba(255, 99, 71, 0.3)",
        },  # Red
    ]

    for quadrant in quadrants:
        fig.add_shape(
            type="rect",
            x0=quadrant["x"][0],
            y0=quadrant["y"][0],
            x1=quadrant["x"][1],
            y1=quadrant["y"][1],
            fillcolor=quadrant["fillcolor"],
            line_color="rgba(0,0,0,0)",
            layer="below",
        )

    # Create a color array based on the date order
    color_array = list(range(len(data)))

    fig.add_trace(
        go.Scatter(
            x=data["cpi_3m_delta"],
            y=data["cli_3m_delta"],
            mode="lines+markers+text",
            name="HumblCompass Data",
            text=[
                d.strftime("%b %Y") if isinstance(d, datetime.date) else ""
                for d in data["date_month_start"]
            ],
            textposition="top center",
            textfont=dict(size=10, color="white"),
            marker=dict(
                size=10,
                color=color_array,
                colorscale=custom_colorscale,
                showscale=False,
            ),
            line=dict(
                color="white",
                shape="spline",
                smoothing=1.3,
            ),
            hovertemplate="<b>%{text}</b><br>CPI 3m Δ: %{x:.2f}<br>CLI 3m Δ: %{y:.2f}<extra></extra>",
        )
    )

    # Add axis lines
    fig.add_hline(y=0, line_dash="solid", line_color="white", opacity=0.7)
    fig.add_vline(x=0, line_dash="solid", line_color="white", opacity=0.7)

    # Calculate the range for x and y axes based on data
    x_min, x_max = data["cpi_3m_delta"].min(), data["cpi_3m_delta"].max()
    y_min, y_max = data["cli_3m_delta"].min(), data["cli_3m_delta"].max()

    # Ensure minimum range of -0.3 to 0.3 on both axes
    x_min = min(x_min, -0.3)
    x_max = max(x_max, 0.3)
    y_min = min(y_min, -0.3)
    y_max = max(y_max, 0.3)

    # Add some padding to the ranges (e.g., 10% on each side)
    x_padding = max((x_max - x_min) * 0.1, 0.05)  # Ensure minimum padding
    y_padding = max((y_max - y_min) * 0.1, 0.05)  # Ensure minimum padding

    fig.update_layout(
        title="humblCOMPASS: CLI 3m Delta vs CPI 3m Delta",
        title_font_color="white",
        xaxis_title="Inflation (CPI) 3-Month Delta",
        yaxis_title="Growth (CLI) 3-Month Delta",
        xaxis=dict(
            color="white",
            showgrid=False,
            zeroline=False,
            range=[x_min - x_padding, x_max + x_padding],
        ),
        yaxis=dict(
            color="white",
            showgrid=False,
            zeroline=False,
            range=[y_min - y_padding, y_max + y_padding],
        ),
        template=template,
        hovermode="closest",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        margin=dict(l=50, r=50, t=50, b=50),
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
