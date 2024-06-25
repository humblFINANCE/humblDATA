"""A module to contain all project-wide constants."""

from typing import Literal

OBB_EQUITY_PRICE_QUOTE_PROVIDERS = Literal[
    "cboe", "fmp", "intrinio", "tmx", "tradier", "yfinance"
]

OBB_EQUITY_PROFILE_PROVIDERS = Literal[
    "finviz", "fmp", "intrinio", "tmx", "yfinance"
]

OBB_ETF_INFO_PROVIDERS = Literal["fmp", "intrinio", "tmx", "yfinance"]

OBB_EQUITY_PRICE_HISTORICAL_PROVIDERS = Literal[
    "alpha_vantage",
    "cboe",
    "fmp",
    "intrinio",
    "polygon",
    "tiingo",
    "tmx",
    "tradier",
    "yfinance",
]

ASSET_CLASSES = Literal[
    "fixed_income",
    "foreign_exchange",
    "equity",
    "commodity",
    "cash",
    "crypto",
    "gold",
    "credit",
]
