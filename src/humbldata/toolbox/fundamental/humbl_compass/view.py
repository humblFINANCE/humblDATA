"""
**Context: Toolbox || Category: Fundamental || Command: humbl_compass**.

The HumblCompass View Module.
"""

import datetime
from typing import List

import plotly.graph_objs as go
import plotly.io as pio
import polars as pl
from plotly.colors import sample_colorscale, sequential

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

    # Calculate the range for x and y axes based on data
    x_min, x_max = data["cpi_3m_delta"].min(), data["cpi_3m_delta"].max()
    y_min, y_max = data["cli_3m_delta"].min(), data["cli_3m_delta"].max()

    # Ensure minimum range of -0.3 to 0.3 on both axes
    x_min = min(x_min if x_min is not None else 0, -0.3)
    x_max = max(x_max if x_max is not None else 0, 0.3)
    y_min = min(y_min if y_min is not None else 0, -0.3)
    y_max = max(y_max if y_max is not None else 0, 0.3)

    # Add some padding to the ranges (e.g., 10% on each side)
    x_padding = max((x_max - x_min) * 0.1, 0.05)  # Ensure minimum padding
    y_padding = max((y_max - y_min) * 0.1, 0.05)  # Ensure minimum padding

    # Calculate tick values (e.g., every 0.1)
    x_ticks = [
        round(i * 0.1, 1)
        for i in range(int(x_min * 10) - 1, int(x_max * 10) + 2)
    ]
    y_ticks = [
        round(i * 0.1, 1)
        for i in range(int(y_min * 10) - 1, int(y_max * 10) + 2)
    ]

    # Add colored quadrants from -10 to 10
    quadrants = [
        {
            "x": [0, 25],
            "y": [0, 25],
            "fillcolor": "rgba(173, 216, 230, 0.3)",
        },  # Light blue
        {
            "x": [-25, 0],
            "y": [0, 25],
            "fillcolor": "rgba(144, 238, 144, 0.3)",
        },  # Green
        {
            "x": [0, 25],
            "y": [-25, 0],
            "fillcolor": "rgba(255, 165, 0, 0.3)",
        },  # Orange
        {
            "x": [-25, 0],
            "y": [-25, 0],
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

    # Check if z-scores are present in the data
    has_zscores = "cli_zscore" in data.columns and "cpi_zscore" in data.columns

    # Modify the hover template based on z-score presence
    hover_template = (
        "<b>%{text}</b><br>" "CPI 3m Δ: %{x:.2f}<br>" "CLI 3m Δ: %{y:.2f}"
    )

    # Prepare customdata for hover if z-scores exist
    customdata = (
        list(zip(data["cpi_zscore"], data["cli_zscore"]))
        if has_zscores
        else None
    )

    if has_zscores:
        hover_template += (
            "<br>CPI Z-Score: %{customdata[0]:.2f}<br>"
            "CLI Z-Score: %{customdata[1]:.2f}"
        )

    hover_template += "<extra></extra>"

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
            textfont={"size": 10, "color": "white"},
            marker={
                "size": 10,
                "color": color_array,
                "colorscale": custom_colorscale,
                "showscale": False,
            },
            line={
                "color": "white",
                "shape": "spline",
                "smoothing": 1.3,
            },
            customdata=customdata,
            hovertemplate=hover_template,
        )
    )

    # Add axis lines with tick marks
    fig.add_shape(
        type="line",
        x0=x_min - x_padding,
        y0=0,
        x1=x_max + x_padding,
        y1=0,
        line=dict(color="white", width=1),
    )
    fig.add_shape(
        type="line",
        x0=0,
        y0=y_min - y_padding,
        x1=0,
        y1=y_max + y_padding,
        line=dict(color="white", width=1),
    )

    # Add tick marks and labels to the x-axis
    for x in x_ticks:
        if x != 0:  # Skip the center point
            fig.add_shape(
                type="line",
                x0=x,
                y0=-0.005,
                x1=x,
                y1=0.005,
                line=dict(color="white", width=1),
            )
            fig.add_annotation(
                x=x,
                y=0,
                text=f"{x:.1f}",
                showarrow=False,
                yshift=-15,
                font=dict(size=8, color="white"),
            )

    # Add tick marks and labels to the y-axis
    for y in y_ticks:
        if y != 0:  # Skip the center point
            fig.add_shape(
                type="line",
                x0=-0.005,
                y0=y,
                x1=0.005,
                y1=y,
                line=dict(color="white", width=1),
            )
            fig.add_annotation(
                x=0,
                y=y,
                text=f"{y:.1f}",
                showarrow=False,
                xshift=-15,
                font=dict(size=8, color="white"),
            )

    # Calculate the center of each visible quadrant
    x_center_pos = (x_max + x_padding + 0) / 2
    x_center_neg = (x_min - x_padding + 0) / 2
    y_center_pos = (y_max + y_padding + 0) / 2
    y_center_neg = (y_min - y_padding + 0) / 2

    # Add quadrant labels
    quadrant_labels = [
        {
            "text": "humblBOOM",
            "x": x_center_neg,
            "y": y_center_pos,
            "color": "rgba(144, 238, 144, 0.5)",  # Changed opacity to 0.5
        },
        {
            "text": "humblBOUNCE",
            "x": x_center_pos,
            "y": y_center_pos,
            "color": "rgba(173, 216, 230, 0.5)",  # Changed opacity to 0.5
        },
        {
            "text": "humblBLOAT",
            "x": x_center_pos,
            "y": y_center_neg,
            "color": "rgba(255, 165, 0, 0.5)",  # Changed opacity to 0.5
        },
        {
            "text": "humblBUST",
            "x": x_center_neg,
            "y": y_center_neg,
            "color": "rgba(255, 99, 71, 0.5)",  # Changed opacity to 0.5
        },
    ]

    for label in quadrant_labels:
        fig.add_annotation(
            x=label["x"],
            y=label["y"],
            text=label["text"],
            showarrow=False,
            font={"size": 20, "color": label["color"]},
            opacity=0.5,  # Changed opacity to 0.5
        )

    # Add custom watermark
    fig.add_annotation(
        x=0,
        y=0,
        text="humblDATA",
        showarrow=False,
        font={"size": 40, "color": "rgba(255, 255, 255, 0.1)"},
        textangle=-25,
        xanchor="center",
        yanchor="middle",
        xref="x",
        yref="y",
    )

    # Create a copy of the template without the watermark
    custom_template = pio.templates[template.value].to_plotly_json()
    if (
        "layout" in custom_template
        and "annotations" in custom_template["layout"]
    ):
        custom_template["layout"]["annotations"] = [
            ann
            for ann in custom_template["layout"]["annotations"]
            if ann.get("name") != "draft watermark"
        ]

    # Update layout
    fig.update_layout(
        title="humblCOMPASS: CLI 3m Delta vs CPI 3m Delta",
        title_font_color="white",
        xaxis_title="Inflation (CPI) 3-Month Delta",
        yaxis_title="Growth (CLI) 3-Month Delta",
        xaxis={
            "color": "white",
            "showgrid": False,
            "zeroline": False,
            "range": [x_min - x_padding, x_max + x_padding],
            "showticklabels": False,  # Hide default tick labels
            "ticks": "",  # Hide default ticks
        },
        yaxis={
            "color": "white",
            "showgrid": False,
            "zeroline": False,
            "range": [y_min - y_padding, y_max + y_padding],
            "showticklabels": False,  # Hide default tick labels
            "ticks": "",  # Hide default ticks
        },
        template=custom_template,  # Use the custom template without watermark
        hovermode="closest",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"},
        margin={"l": 50, "r": 50, "t": 50, "b": 50},
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
