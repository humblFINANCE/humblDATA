import polars as pl
import pytest

from humbldata.portfolio.analytics.watchlist.model import watchlist_table_engine
from humbldata.toolbox.toolbox_controller import Toolbox


@pytest.mark.asyncio
async def test_watchlist_table_engine_integration():
    # Test data
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN"]

    # Run the function
    result = await watchlist_table_engine(
        symbols=symbols,
        membership="anonymous",
    )

    # Collect the result
    result_df = result.collect()

    # Assert that the result is a LazyFrame
    assert isinstance(result, pl.LazyFrame)

    # Assert that all expected columns are present
    expected_columns = [
        "date",
        "symbol",
        "buy_price",
        "last_price",
        "sell_price",
        "ud_pct",
        "ud_ratio",
        "sector",
        "asset_class",
    ]
    assert set(result_df.columns) == set(expected_columns)

    # Assert that the number of rows matches the number of input symbols
    assert len(result_df) == len(symbols)

    # Assert that all input symbols are present in the result
    assert set(result_df["symbol"]) == set(symbols)

    # Additional assertions to check data integrity
    assert not result_df["date"].is_null().any()
    assert not result_df["buy_price"].is_null().any()
    assert not result_df["last_price"].is_null().any()
    assert not result_df["sell_price"].is_null().any()
    assert not result_df["ud_pct"].is_null().any()
    assert not result_df["ud_ratio"].is_null().any()
    assert not result_df["sector"].is_null().any()
    assert not result_df["asset_class"].is_null().any()

    # Print the result for visual inspection
    print(result_df)
