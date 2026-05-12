"""Query parameters for OpenBB equity price quote endpoints."""

# ruff: noqa: INP001

from typing import Literal

from humbldata.core.standard_models.abstract.query_params import QueryParams


class EquityPriceQuoteQueryParams(QueryParams):
    """
    Query parameters for the OpenBB equity.price.quote endpoint.

    Parameters
    ----------
    symbol : str | list[str]
        Symbol(s) to get data for. Multiple comma separated items allowed for
        provider(s): fmp, intrinio, yfinance.
    provider : Literal['fmp', 'intrinio', 'yfinance'] | None, optional
        The provider to use. If None, the default priority list is used:
        fmp, intrinio, yfinance.
    source
        Source of the data. Only used for provider 'intrinio'.
    """

    symbol: str | list[str]
    provider: Literal["fmp", "intrinio", "yfinance"] | None = "yfinance"
    source: (
        Literal[
            "iex",
            "bats",
            "bats_delayed",
            "utp_delayed",
            "cta_a_delayed",
            "cta_b_delayed",
            "intrinio_mx",
            "intrinio_mx_plus",
            "delayed_sip",
        ]
        | None
    ) = None
