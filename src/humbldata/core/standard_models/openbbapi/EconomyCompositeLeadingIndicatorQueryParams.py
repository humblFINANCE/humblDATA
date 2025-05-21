import datetime as dt
from typing import Literal

from pydantic import Field

from humbldata.core.standard_models.abstract.query_params import QueryParams


class EconomyCompositeLeadingIndicatorQueryParams(QueryParams):
    """
    QueryParams model for Composite Leading Indicator (CLI) data.

    Parameters
    ----------
    provider : str | None
        The provider to use, by default None. If None, the priority list configured in the settings is used. Default priority: oecd.
    start_date : dt.date | str | None
        Start date of the data, in YYYY-MM-DD format.
    end_date : dt.date | str | None
        End date of the data, in YYYY-MM-DD format.
    country : Literal[...] | str
        Country to get the CLI for, default is G20. Multiple comma separated items allowed. (provider: oecd)
    adjustment : Literal['amplitude', 'normalized'] | None
        Adjustment of the data, either 'amplitude' or 'normalized'. Default is amplitude. (provider: oecd)
    growth_rate : bool | None
        Return the 1-year growth rate (%) of the CLI, default is False. (provider: oecd)
    """

    provider: str | None = Field(
        default=None,
        description="The provider to use, by default None. If None, the priority list configured in the settings is used. Default priority: oecd.",
    )
    start_date: dt.date | str | None = Field(
        default=None,
        description="Start date of the data, in YYYY-MM-DD format.",
    )
    end_date: dt.date | str | None = Field(
        default=None,
        description="End date of the data, in YYYY-MM-DD format.",
    )
    country: (
        Literal[
            "g20",
            "g7",
            "asia5",
            "north_america",
            "europe4",
            "australia",
            "brazil",
            "canada",
            "china",
            "france",
            "germany",
            "india",
            "indonesia",
            "italy",
            "japan",
            "mexico",
            "south_africa",
            "south_korea",
            "spain",
            "turkey",
            "united_kingdom",
            "united_states",
            "all",
        ]
        | str
    ) = Field(
        default="g20",
        description="Country to get the CLI for, default is G20. Multiple comma separated items allowed. (provider: oecd)",
    )
    adjustment: Literal["amplitude", "normalized"] | None = Field(
        default="amplitude",
        description="Adjustment of the data, either 'amplitude' or 'normalized'. Default is amplitude. (provider: oecd)",
    )
    growth_rate: bool | None = Field(
        default=False,
        description="Return the 1-year growth rate (%) of the CLI, default is False. (provider: oecd)",
    )
