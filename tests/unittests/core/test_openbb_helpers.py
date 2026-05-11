import asyncio
from unittest.mock import AsyncMock

import polars as pl
import pytest

from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.utils.openbb_helpers import (
    aget_equity_sector,
    aget_etf_category,
    aget_latest_price,
    obb_login,
)


def api_response(data: dict[str, list[object]]) -> HumblObject[pl.LazyFrame]:
    return HumblObject(results=pl.LazyFrame(data))


def test_aget_latest_price_mocks_equity_price_quote(monkeypatch):
    fetch_data = AsyncMock(
        return_value=api_response(
            {
                "symbol": ["AAPL", "XLE"],
                "asset_type": ["EQUITY", "ETF"],
                "last_price": [190.0, None],
                "prev_close": [188.0, 88.0],
            }
        )
    )
    monkeypatch.setattr(
        "humbldata.core.utils.openbb_helpers.OpenBBAPIClient.fetch_data",
        fetch_data,
    )

    result = asyncio.run(
        aget_latest_price(pl.Series("symbol", ["AAPL", "XLE"]))
    )

    assert result.collect().to_dict(as_series=False) == {
        "last_price": [190.0, 88.0],
        "symbol": ["AAPL", "XLE"],
    }
    fetch_data.assert_awaited_once()
    _, kwargs = fetch_data.call_args
    assert kwargs["obb_path"] == "equity.price.quote"
    assert kwargs["api_query_params"].symbol == ["AAPL", "XLE"]
    assert kwargs["api_query_params"].provider == "yfinance"


def test_aget_equity_sector_mocks_equity_profile(monkeypatch):
    fetch_data = AsyncMock(
        return_value=api_response(
            {
                "symbol": ["AAPL", "NVDA"],
                "sector": ["Technology", "Technology"],
            }
        )
    )
    monkeypatch.setattr(
        "humbldata.core.utils.openbb_helpers.OpenBBAPIClient.fetch_data",
        fetch_data,
    )

    result = asyncio.run(aget_equity_sector(["AAPL", "NVDA"], provider="fmp"))

    assert result.collect().to_dict(as_series=False) == {
        "symbol": ["AAPL", "NVDA"],
        "sector": ["Technology", "Technology"],
    }
    fetch_data.assert_awaited_once()
    _, kwargs = fetch_data.call_args
    assert kwargs["obb_path"] == "equity.profile"
    assert kwargs["api_query_params"].symbol == ["AAPL", "NVDA"]
    assert kwargs["api_query_params"].provider == "fmp"


def test_aget_etf_category_mocks_etf_info(monkeypatch):
    fetch_data = AsyncMock(
        return_value=api_response(
            {
                "symbol": ["XLE"],
                "category": ["Equity Energy"],
            }
        )
    )
    monkeypatch.setattr(
        "humbldata.core.utils.openbb_helpers.OpenBBAPIClient.fetch_data",
        fetch_data,
    )

    result = asyncio.run(
        aget_etf_category(["AAPL", "XLE"], provider="yfinance")
    )

    assert result.collect().to_dict(as_series=False) == {
        "symbol": ["AAPL", "XLE"],
        "category": [None, "Equity Energy"],
    }
    fetch_data.assert_awaited_once()
    _, kwargs = fetch_data.call_args
    assert kwargs["obb_path"] == "etf.info"
    assert kwargs["api_query_params"].symbol == ["XLE"]
    assert kwargs["api_query_params"].provider == "yfinance"


def test_obb_login_returns_false_and_warns():
    with pytest.warns(
        Warning,
        match="obb_login is deprecated",
    ):
        assert obb_login("unused-token") is False
