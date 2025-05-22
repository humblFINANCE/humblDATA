from pydantic import field_validator

from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.utils.constants import OBB_ETF_INFO_PROVIDERS


class EtfInfoQueryParams(QueryParams):
    """
    Query parameters for the OpenBB etf.info endpoint.

    Parameters
    ----------
    symbol : str | list[str]
        Symbol(s) to get data for. (ETF) Multiple comma separated items allowed for provider(s): fmp, intrinio, yfinance.
    provider : OBB_ETF_INFO_PROVIDERS | None, optional
        The provider to use. If None, the default provider priority is used: fmp, intrinio, yfinance.
    """

    symbol: str | list[str]
    provider: OBB_ETF_INFO_PROVIDERS | None = None

    @field_validator("symbol", mode="before")
    @classmethod
    def ensure_list_or_str(cls, v):
        if isinstance(v, list | str):
            return v
        msg = "symbol must be a str or list of str"
        raise TypeError(msg)
