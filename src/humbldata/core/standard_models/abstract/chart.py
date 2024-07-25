from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChartTemplate(str, Enum):
    """
    Chart format.

    Available options:
    - plotly
    - humbl_light
    - humbl_dark
    - plotly_light
    - plotly_dark
    - ggplot2
    - seaborn
    - simple_white
    - presentation
    - xgridoff
    - ygridoff
    - gridon
    - none
    """

    plotly = "plotly"
    humbl_light = "humbl_light"
    humbl_dark = "humbl_dark"
    plotly_light = "plotly_light"
    plotly_dark = "plotly_dark"
    ggplot2 = "ggplot2"
    seaborn = "seaborn"
    simple_white = "simple_white"
    presentation = "presentation"
    xgridoff = "xgridoff"
    ygridoff = "ygridoff"
    gridon = "gridon"
    none = "none"


class Chart(BaseModel):
    """a Chart Object that is returned from a View."""

    content: str | None = Field(
        default=None,
        description="Raw textual representation of the chart.",
    )
    theme: ChartTemplate | None = Field(
        default=ChartTemplate.plotly,
        description="Complementary attribute to the `content` attribute. It specifies the format of the chart.",
    )
    fig: Any | None = Field(
        default=None,
        description="The figure object.",
        # json_schema_extra={"exclude_from_api": True},
    )
    model_config = ConfigDict(validate_assignment=True)

    def __repr__(self) -> str:
        """Human readable representation of the object."""
        items = [
            f"{k}: {v}"[:83] + ("..." if len(f"{k}: {v}") > 83 else "")
            for k, v in self.model_dump().items()
        ]

        return f"{self.__class__.__name__}\n\n" + "\n".join(items)
