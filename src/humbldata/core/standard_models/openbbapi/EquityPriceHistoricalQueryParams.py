import datetime as dt
from typing import Literal

from pydantic import Field

from humbldata.core.standard_models.abstract.query_params import QueryParams


class EquityPriceHistoricalQueryParams(QueryParams):
    """
    QueryParams model for Equity Historical Price data.

    Parameters
    ----------
    provider : str
        The provider to use, by default None. If None, the priority list configured in the settings is used. Default priority: fmp, intrinio, polygon, tiingo, yfinance.
    symbol : str | list[str]
        Symbol to get data for. Multiple comma separated items allowed for provider(s): fmp, polygon, tiingo, yfinance.
    start_date : dt.date | None | str
        Start date of the data, in YYYY-MM-DD format.
    end_date : dt.date | None | str
        End date of the data, in YYYY-MM-DD format.
    interval : str
        Time interval of the data to return. (provider: fmp, intrinio, polygon, tiingo, yfinance)
        Choices for fmp: '1m', '5m', '15m', '30m', '1h', '4h', '1d'
        Choices for intrinio: '1m', '5m', '10m', '15m', '30m', '60m', '1h', '1d', '1W', '1M', '1Q', '1Y'
        Choices for yfinance: '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1W', '1M', '1Q'
    start_time : dt.time | None
        Return intervals starting at the specified time on the `start_date` formatted as 'HH:MM:SS'. (provider: intrinio)
    end_time : dt.time | None
        Return intervals stopping at the specified time on the `end_date` formatted as 'HH:MM:SS'. (provider: intrinio)
    timezone : str | None
        Timezone of the data, in the IANA format (Continent/City). (provider: intrinio)
    source : Literal['realtime', 'delayed', 'nasdaq_basic'] | None
        The source of the data. (provider: intrinio)
    adjustment : str | None
        The adjustment factor to apply. Default is splits only. (provider: polygon, yfinance)
        Choices for polygon: 'splits_only', 'unadjusted'
        Choices for yfinance: 'splits_only', 'splits_and_dividends'
    extended_hours : bool | None
        Include Pre and Post market data. (provider: polygon, yfinance)
    sort : Literal['asc', 'desc'] | None
        Sort order of the data. This impacts the results in combination with the 'limit' parameter. The results are always returned in ascending order by date. (provider: polygon)
    limit : int | None
        The number of data entries to return. (provider: polygon)
    include_actions : bool | None
        Include dividends and stock splits in results. (provider: yfinance)
    """

    provider: str | None = Field(
        default=None,
        description="The provider to use, by default None. If None, the priority list configured in the settings is used. Default priority: fmp, intrinio, polygon, tiingo, yfinance.",
    )
    symbol: str | list[str] = Field(
        ...,
        description="Symbol to get data for. Multiple comma separated items allowed for provider(s): fmp, polygon, tiingo, yfinance.",
    )
    start_date: dt.date | str | None = Field(
        default=None,
        description="Start date of the data, in YYYY-MM-DD format.",
    )
    end_date: dt.date | str | None = Field(
        default=None,
        description="End date of the data, in YYYY-MM-DD format.",
    )
    interval: str | None = Field(
        default=None,
        description="Time interval of the data to return. (provider: fmp, intrinio, polygon, tiingo, yfinance)",
    )
    start_time: dt.time | None = Field(
        default=None,
        description="Return intervals starting at the specified time on the `start_date` formatted as 'HH:MM:SS'. (provider: intrinio)",
    )
    end_time: dt.time | None = Field(
        default=None,
        description="Return intervals stopping at the specified time on the `end_date` formatted as 'HH:MM:SS'. (provider: intrinio)",
    )
    timezone: str | None = Field(
        default=None,
        description="Timezone of the data, in the IANA format (Continent/City). (provider: intrinio)",
    )
    source: Literal["realtime", "delayed", "nasdaq_basic"] | None = Field(
        default=None,
        description="The source of the data. (provider: intrinio)",
    )
    adjustment: str | None = Field(
        default=None,
        description="The adjustment factor to apply. Default is splits only. (provider: polygon, yfinance)",
    )
    extended_hours: bool | None = Field(
        default=None,
        description="Include Pre and Post market data. (provider: polygon, yfinance)",
    )
    sort: Literal["asc", "desc"] | None = Field(
        default=None,
        description="Sort order of the data. This impacts the results in combination with the 'limit' parameter. The results are always returned in ascending order by date. (provider: polygon)",
    )
    limit: int | None = Field(
        default=None,
        description="The number of data entries to return. (provider: polygon)",
    )
    include_actions: bool | None = Field(
        default=None,
        description="Include dividends and stock splits in results. (provider: yfinance)",
    )
