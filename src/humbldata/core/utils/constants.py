"""A module to contain all project-wide constants."""

from typing import Dict, Literal
import re

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
    "Fixed Income",
    "Foreign Exchange",
    "Equity",
    "Commodity",
    "Cash",
    "Crypto",
    "Gold",
    "Credit",
]
ASSET_CLASS_MAPPING: dict[str, ASSET_CLASSES] = {
    "Fixed Income": "Fixed Income",
    "Ultrashort Bond": "Fixed Income",
    "Bond": "Fixed Income",
    r".*\s?Bond.*": "Fixed Income",
    "Foreign Exchange": "Foreign Exchange",
    "Single Currency": "Foreign Exchange",
    "Forex": "Foreign Exchange",
    "FX": "Foreign Exchange",
    "Equity": "Equity",
    "Stocks": "Equity",
    "Commodity": "Commodity",
    "Commodities": "Commodity",
    r".*Commodities.*": "Commodity",
    "Cash": "Cash",
    "Money Market": "Cash",
    "Crypto": "Crypto",
    "Digital Assets": "Crypto",
    "Cryptocurrency": "Crypto",
    "Gold": "Gold",
    "Precious Metals": "Gold",
    "Credit": "Credit",
    "Debt": "Credit",
}

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
GICS_SECTOR_MAPPING: dict[str, GICS_SECTORS] = {
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
    "Materials": "Materials",
    "Basic Materials": "Materials",
    "Real Estate": "Real Estate",
    "Utilities": "Utilities",
}
