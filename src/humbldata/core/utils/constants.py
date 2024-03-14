"""A module to contain all project-wide constants."""

from typing import Literal

OBB_EQUITY_PRICE_QUOTE_PROVIDERS = Literal[
    "cboe", "fmp", "intrinio", "tmx", "tradier", "yfinance"
]

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
