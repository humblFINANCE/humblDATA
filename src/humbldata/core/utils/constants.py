"""A module to contain all project-wide constants."""

from typing import Dict, Literal

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
    "Fixed income",
    "Foreign exchange",
    "Equity",
    "Commodity",
    "Cash",
    "Crypto",
    "Gold",
    "Credit",
]
GICS_SECTORS = Literal[
    "Communication Services",
    "Consumer Cyclical",
    "Consumer Defensive",
    "Energy",
    "Financials",
    "Health Care",
    "Industrials",
    "Technology",
    "Materials",
    "Real Estate",
    "Utilities",
]
EQUITY_SECTOR_MAPPING: dict[str, GICS_SECTORS] = {
    "Communication Services": "Communication Services",
    "Communications": "Communication Services",
    "Communication": "Communication Services",
    "Consumer Cyclical": "Consumer Cyclical",
    "Consumer Discretionary": "Consumer Cyclical",
    "Consumer Defensive": "Consumer Defensive",
    "Consumer Staples": "Consumer Defensive",
    "Energy": "Energy",
    "Equity Energy": "Energy",
    "Financials": "Financials",
    "Financial Service": "Financials",
    "Financial": "Financials",
    "Health Care": "Health Care",
    "Healthcare": "Health Care",
    "Industrials": "Industrials",
    "Technology": "Technology",
    "Tech": "Technology",
    "Materials": "Materials",
    "Basic Materials": "Materials",
    "Real Estate": "Real Estate",
    "Utilities": "Utilities",
}
