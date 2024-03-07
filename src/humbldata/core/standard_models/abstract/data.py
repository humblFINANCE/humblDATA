"""A wrapper around OpenBB Data Standardized Model to use with humbldata."""

from openbb_core.provider.abstract.data import (
    Data as OpenBBData,
)


class Data(OpenBBData):
    """
    An abstract standard_model to represent a base Data Model.

    The Data Model should be used to define the data that is being
    collected and analyzed in a `context.category.command` call.

    This Data model is meant to be inherited and built upon by other
    standard_models for a specific context.

    Example
    -------
    ```py
    total_time = f"{end_time - start_time:.3f}"
    class EquityHistoricalData(Data):

    date: Union[dateType, datetime] = Field(
        description=DATA_DESCRIPTIONS.get("date", "")
    )
    open: float = Field(description=DATA_DESCRIPTIONS.get("open", ""))
    high: float = Field(description=DATA_DESCRIPTIONS.get("high", ""))
    low: float = Field(description=DATA_DESCRIPTIONS.get("low", ""))
    close: float = Field(description=DATA_DESCRIPTIONS.get("close", ""))
    volume: Optional[Union[float, int]] = Field(
        default=None, description=DATA_DESCRIPTIONS.get("volume", "")
    )

    @field_validator("date", mode="before", check_fields=False)
    def date_validate(cls, v):  # pylint: disable=E0213
        v = parser.isoparse(str(v))
        if v.hour == 0 and v.minute == 0:
            return v.date()
        return v

    ```
    """
