from typing import Any, ClassVar, Generic, TypeVar,

from pydantic import BaseModel, Field, PrivateAttr

from humbldata.core.standard_models.abstract.tagged import Tagged
from humbldata.core.standard_models.abstract.chart import Chart
from humbldata.core.standard_models.abstract.warnings import Warning_

T = TypeVar("T")


class HumblObject(Tagged, Generic[T]):
    """HumblObject is the base class for all dta returned from the Toolbox."""

    _user_settings: ClassVar[BaseModel | None] = None
    _system_settings: ClassVar[BaseModel | None] = None

    results: T | None = Field(
        default=None,
        description="Serializable results.",
    )
    provider: str | None = Field(  # type: ignore
        default=None,
        description="Provider name.",
    )
    warnings: list[Warning_] | None = Field(
        default=None,
        description="List of warnings.",
    )
    chart: Chart | None = Field(
        default=None,
        description="Chart object.",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Extra info.",
    )

    _context_params: dict[str, Any] | None = PrivateAttr(
        default_factory=dict,
    )
    _command_params: dict[str, Any] | None = PrivateAttr(
        default_factory=dict,
    )
