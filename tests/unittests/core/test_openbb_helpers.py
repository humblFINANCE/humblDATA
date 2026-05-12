"""Tests for OpenBB helper API-client wrappers."""

import asyncio
from unittest.mock import AsyncMock

import polars as pl

from humbldata.core.utils import openbb_helpers


class MockOpenBBResponse:
    """Minimal response object returned by the mocked OpenBB API client."""

    def __init__(self, frame: pl.DataFrame | None):
        self._frame = frame
        self.results = None if frame is None else frame.to_dicts()

    def to_polars(self, *, collect: bool = True) -> pl.LazyFrame:
        """Return the mocked response data as a lazy frame."""
        assert collect is False
        if self._frame is None:
            return pl.LazyFrame([])
        return self._frame.lazy()


def patch_openbb_client(monkeypatch, response: MockOpenBBResponse) -> AsyncMock:
    """Patch OpenBBAPIClient and return its fetch_data mock."""
    fetch_data = AsyncMock(return_value=response)

    class MockOpenBBAPIClient:
        def __init__(self):
            self.fetch_data = fetch_data

    monkeypatch.setattr(openbb_helpers, "OpenBBAPIClient", MockOpenBBAPIClient)
    return fetch_data


def test_aget_latest_price_fetches_quote_data(monkeypatch):
    """Latest price helper fetches equity quote data through the API client."""
    response = MockOpenBBResponse(
        pl.DataFrame(
            {
                "symbol": ["AAPL", "SPY"],
                "asset_type": ["EQUITY", "ETF"],
                "last_price": [191.25, 562.10],
                "prev_close": [190.75, 560.50],
            }
        )
    )
    fetch_data = patch_openbb_client(monkeypatch, response)

    prices = asyncio.run(
        openbb_helpers.aget_latest_price(
            pl.Series("symbol", ["AAPL", "SPY"]), provider="yfinance"
        )
    )

    assert prices.collect().to_dicts() == [
        {"last_price": 191.25, "symbol": "AAPL"},
        {"last_price": 560.50, "symbol": "SPY"},
    ]
    fetch_data.assert_awaited_once()
    _, kwargs = fetch_data.call_args
    assert kwargs["obb_path"] == "equity.price.quote"
    assert kwargs["api_query_params"].symbol == ["AAPL", "SPY"]
    assert kwargs["api_query_params"].provider == "yfinance"


def test_aget_latest_price_ignores_unsupported_provider(monkeypatch):
    """Unsupported quote providers are omitted from query params."""
    response = MockOpenBBResponse(
        pl.DataFrame(
            {
                "symbol": ["AAPL"],
                "last_price": [191.25],
            }
        )
    )
    fetch_data = patch_openbb_client(monkeypatch, response)

    prices = asyncio.run(
        openbb_helpers.aget_latest_price("AAPL", provider="tmx")
    )

    assert prices.collect().to_dicts() == [
        {"symbol": "AAPL", "last_price": 191.25}
    ]
    _, kwargs = fetch_data.call_args
    assert kwargs["obb_path"] == "equity.price.quote"
    assert kwargs["api_query_params"].symbol == "AAPL"
    assert kwargs["api_query_params"].provider is None


def test_aget_equity_sector_fetches_profile_data(monkeypatch):
    """Equity sector helper fetches profile data through the API client."""
    response = MockOpenBBResponse(
        pl.DataFrame(
            {
                "symbol": ["AAPL", "MSFT"],
                "sector": ["Technology", "Technology"],
                "industry": ["Consumer Electronics", "Software"],
            }
        )
    )
    fetch_data = patch_openbb_client(monkeypatch, response)

    sectors = asyncio.run(
        openbb_helpers.aget_equity_sector(["AAPL", "MSFT"], provider="fmp")
    )

    assert sectors.collect().to_dicts() == [
        {"symbol": "AAPL", "sector": "Technology"},
        {"symbol": "MSFT", "sector": "Technology"},
    ]
    fetch_data.assert_awaited_once()
    _, kwargs = fetch_data.call_args
    assert kwargs["obb_path"] == "equity.profile"
    assert kwargs["api_query_params"].symbol == ["AAPL", "MSFT"]
    assert kwargs["api_query_params"].provider == "fmp"


def test_aget_equity_sector_returns_null_sector_when_missing(
    monkeypatch,
):
    """Return null sectors when profile data omits them."""
    response = MockOpenBBResponse(
        pl.DataFrame(
            {
                "symbol": ["SPY"],
                "name": ["SPDR S&P 500 ETF Trust"],
            }
        )
    )
    patch_openbb_client(monkeypatch, response)

    sectors = asyncio.run(openbb_helpers.aget_equity_sector("SPY"))

    assert sectors.collect().to_dicts() == [{"symbol": "SPY", "sector": None}]


def test_aget_etf_category_fetches_only_known_etfs(monkeypatch):
    """ETF category helper fetches API data only for recognized ETFs."""
    response = MockOpenBBResponse(
        pl.DataFrame(
            {
                "symbol": ["SPY"],
                "category": ["Large Blend"],
                "name": ["SPDR S&P 500 ETF Trust"],
            }
        )
    )
    fetch_data = patch_openbb_client(monkeypatch, response)

    categories = asyncio.run(
        openbb_helpers.aget_etf_category(["SPY", "AAPL"], provider="fmp")
    )

    assert categories.collect().to_dicts() == [
        {"symbol": "SPY", "category": "Large Blend"},
        {"symbol": "AAPL", "category": None},
    ]
    fetch_data.assert_awaited_once()
    _, kwargs = fetch_data.call_args
    assert kwargs["obb_path"] == "etf.info"
    assert kwargs["api_query_params"].symbol == ["SPY"]
    assert kwargs["api_query_params"].provider == "fmp"


def test_aget_etf_category_skips_api_call_when_no_symbols_are_etfs(
    monkeypatch,
):
    """ETF category helper avoids API calls when no symbols are known ETFs."""
    fetch_data = patch_openbb_client(monkeypatch, MockOpenBBResponse(None))

    categories = asyncio.run(openbb_helpers.aget_etf_category(["AAPL", "MSFT"]))

    assert categories.collect().to_dicts() == [
        {"symbol": "AAPL", "category": None},
        {"symbol": "MSFT", "category": None},
    ]
    fetch_data.assert_not_awaited()
