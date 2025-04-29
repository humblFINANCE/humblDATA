import datetime

import polars as pl
import pytest
from humbldata.core.standard_models.abstract.humblobject import HumblObject

from humbldata.core.standard_models.portfolio import PortfolioQueryParams
from humbldata.core.standard_models.portfolio.analytics.watchlist_table import (
    WatchlistTableData,
    WatchlistTableFetcher,
    WatchlistTableQueryParams,
)


@pytest.mark.parametrize(
    ("input_symbols", "expected_symbols"),
    [
        ("AAPL", ["AAPL"]),
        ("aapl,msft", ["AAPL", "MSFT"]),
        (["aapl", "MSFT"], ["AAPL", "MSFT"]),
        ({"tsla", "amzn"}, ["TSLA", "AMZN"]),
        ("GOOGL,FB,AMZN", ["GOOGL", "FB", "AMZN"]),
        (["nvda", "amd", "intc"], ["NVDA", "AMD", "INTC"]),
        ({"JPM", "BAC", "WFC"}, ["JPM", "BAC", "WFC"]),
        ("", []),
        ([], []),
        (set(), []),
    ],
)
def test_watchlist_table_queryparams(input_symbols, expected_symbols):
    """Test Custom `@field_validator()` on `symbols` field."""
    params = WatchlistTableQueryParams(symbols=input_symbols)
    assert set(params.symbols) == set(expected_symbols)


@pytest.fixture(params=["small_dataset", "large_dataset"])
def watchlist_table_data(request):
    base_data = {
        "symbol": ["AAPL", "MSFT", "GOOGL", "SPY", "QQQ"],
        "last_price": [150.0, 300.0, 2800.0, 400.0, 350.0],
        "buy_price": [145.0, 290.0, 2750.0, 395.0, 345.0],
        "sell_price": [155.0, 310.0, 2850.0, 405.0, 355.0],
        "ud_pct": ["3.33%", "3.33%", "3.57%", "1.25%", "1.43%"],
        "ud_ratio": [1.5, 1.5, 1.4, 1.2, 1.3],
        "asset_class": ["Equity", "Equity", "Equity", "ETF", "ETF"],
        "sector": [
            "Technology",
            "Technology",
            "Communication Services",
            "Broad Market",
            "Technology",
        ],
    }

    if request.param == "large_dataset":
        base_data["symbol"].extend(["AMZN", "TSLA", "FB", "IWM", "VTI"])
        base_data["last_price"].extend([3200.0, 700.0, 350.0, 180.0, 220.0])
        base_data["buy_price"].extend([3100.0, 680.0, 340.0, 175.0, 215.0])
        base_data["sell_price"].extend([3300.0, 720.0, 360.0, 185.0, 225.0])
        base_data["ud_pct"].extend(
            ["3.13%", "2.94%", "2.86%", "2.78%", "2.27%"]
        )
        base_data["ud_ratio"].extend([1.6, 1.7, 1.8, 1.4, 1.5])
        base_data["asset_class"].extend(
            ["Equity", "Equity", "Equity", "ETF", "ETF"]
        )
        base_data["sector"].extend(
            [
                "Consumer Discretionary",
                "Consumer Discretionary",
                "Communication Services",
                "Small Cap",
                None,
            ]
        )

    return pl.LazyFrame(base_data)


def test_watchlist_table_data_validation(watchlist_table_data):
    WatchlistTableData(watchlist_table_data.collect())


@pytest.mark.asyncio()
async def test_watchlist_table_fetcher():
    """Test the integration of WatchlistTableFetcher with actual data fetching."""
    fetcher = WatchlistTableFetcher(
        context_params=PortfolioQueryParams(symbols=["AAPL", "MSFT"]),
        command_params=None,
    )

    result = await fetcher.fetch_data()
    data = result.to_polars()

    assert not data.is_empty()
    assert "symbol" in data.columns
    assert "last_price" in data.columns
    assert "buy_price" in data.columns
    assert "sell_price" in data.columns
    assert "ud_pct" in data.columns
    assert "ud_ratio" in data.columns
    assert "asset_class" in data.columns
    assert "sector" in data.columns

    assert set(data["symbol"]) == {"AAPL", "MSFT"}


@pytest.mark.asyncio()
async def test_watchlist_table_fetcher_integration():
    """Test the WatchlistTableFetcher and validate the data with WatchlistTableData."""
    fetcher = WatchlistTableFetcher(
        context_params=PortfolioQueryParams(symbols=["AAPL", "MSFT"]),
        command_params=None,
    )

    result = await fetcher.fetch_data()

    assert isinstance(result, HumblObject)
    data = result.to_polars()

    assert not data.is_empty()
    assert len(data) == 2
    assert set(data["symbol"]) == {"AAPL", "MSFT"}

    for column in ["last_price", "buy_price", "sell_price", "ud_ratio"]:
        assert not data[column].is_null().any()

    for column in ["ud_pct", "asset_class", "sector"]:
        assert not data[column].is_null().any()
        assert data[column].dtype == pl.Utf8
