from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChartFormat(str, Enum):
    """Chart format."""

    plotly = "plotly"


class Chart(BaseModel):
    """a Chart Object that is returned from a View."""

    content: dict[str, Any] | None = Field(
        default=None,
        description="Raw textual representation of the chart.",
    )
    format: ChartFormat | None = Field(
        default=ChartFormat.plotly,
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
