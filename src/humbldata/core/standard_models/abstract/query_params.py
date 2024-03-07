"""A wrapper around OpenBB QueryParams Standardized Model to use with humbldata."""  # noqa: W505

from openbb_core.provider.abstract.query_params import (
    QueryParams as OpenBBQueryParams,
)


class QueryParams(OpenBBQueryParams):
    """
    An abstract standard_model to represent a base QueryParams Data.

    QueryParams model should be used to define the query parameters for a
    `context.category.command` call.

    This QueryParams model is meant to be inherited and built upon by other
    standard_models for a specific context.

    Examples
    --------
    ```py
    class EquityHistoricalQueryParams(QueryParams):

        symbol: str = Field(description=QUERY_DESCRIPTIONS.get("symbol", ""))
        interval: Optional[str] = Field(
            default="1d",
            description=QUERY_DESCRIPTIONS.get("interval", ""),
        )
        start_date: Optional[dateType] = Field(
            default=None,
            description=QUERY_DESCRIPTIONS.get("start_date", ""),
        )
        end_date: Optional[dateType] = Field(
            default=None,
            description=QUERY_DESCRIPTIONS.get("end_date", ""),
        )

        @field_validator("symbol", mode="before", check_fields=False)
        @classmethod
        def upper_symbol(cls, v: Union[str, List[str], Set[str]]):
            if isinstance(v, str):
                return v.upper()
            return ",".join([symbol.upper() for symbol in list(v)])
    ```

    This would create a class that would be used to query historical price data
    for equities from any given command.

    This could then be used to create a
    `MandelbrotChannelEquityHistoricalQueryParams` that would define what query
    parameters are needed for the Mandelbrot Channel command.
    """
