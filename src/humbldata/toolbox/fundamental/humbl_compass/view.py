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

    # Use only a portion of the colorscale (e.g., from 20% to 80%)
    start = 0.2
    end = 0.8
    custom_colorscale = sample_colorscale(
        full_color_scale,
        [i / 100 for i in range(int(start * 100), int(end * 100) + 1, 10)],
    )

    fig = go.Figure()

    # Calculate the range for x and y axes
    x_max = max(
        abs(float(data["cpi_3m_delta"].max() or 0)),
        abs(float(data["cpi_3m_delta"].min() or 0)),
    )
    y_max = max(
        abs(float(data["cli_3m_delta"].max() or 0)),
        abs(float(data["cli_3m_delta"].min() or 0)),
    )
    max_range = max(x_max, y_max)

    # Add asymmetric buffers to the x-axis range
    x_buffer_right = max_range * 0.05
    x_buffer_left = max_range * 0.15  # Larger buffer on the left side
    x_axis_range = [-max_range - x_buffer_left, max_range + x_buffer_right]

    # Calculate a tighter y-axis range
    y_data_max = float(data["cli_3m_delta"].max() or 0)
    y_data_min = float(data["cli_3m_delta"].min() or 0)
    y_buffer = (y_data_max - y_data_min) * 0.1  # 10% buffer
    y_axis_range = [y_data_min - y_buffer, y_data_max + y_buffer]

    # Extend the quadrants beyond the data range
    quadrant_extension = max_range * 0.1
    extended_max_range = max_range + quadrant_extension

    # Add colored quadrants
    quadrants = [
        {
            "x": [0, extended_max_range],
            "y": [0, extended_max_range],
            "fillcolor": "rgba(173, 216, 230, 0.3)",
        },  # Light blue
        {
            "x": [-extended_max_range, 0],
            "y": [0, extended_max_range],
            "fillcolor": "rgba(144, 238, 144, 0.3)",
        },  # Green
        {
            "x": [0, extended_max_range],
            "y": [-extended_max_range, 0],
            "fillcolor": "rgba(255, 165, 0, 0.3)",
        },  # Orange
        {
            "x": [-extended_max_range, 0],
            "y": [-extended_max_range, 0],
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
                showscale=False,  # This line removes the colorbar
            ),
            line=dict(
                color="white",
                shape="spline",  # This line smooths the curve
                smoothing=1.3,  # Adjust this value to control the smoothness (0 to 1.3)
            ),
            hovertemplate="<b>%{text}</b><br>CPI 3m Δ: %{x:.2f}<br>CLI 3m Δ: %{y:.2f}<extra></extra>",
        )
    )

    # Change the axis lines from dashed to solid
    fig.add_hline(y=0, line_dash="solid", line_color="white", opacity=0.7)
    fig.add_vline(x=0, line_dash="solid", line_color="white", opacity=0.7)

    fig.update_layout(
        title="humblCOMPASS: CLI 3m Delta vs CPI 3m Delta",
        title_font_color="white",
        xaxis_title="Inflation (CPI) 3-Month Delta",
        yaxis_title="Growth (CLI) 3-Month Delta",
        xaxis=dict(
            range=x_axis_range,
            color="white",
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(
            range=y_axis_range,
            color="white",
            showgrid=False,
            zeroline=False,
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
