import polars as pl
import pytest
from _pytest.fixtures import FixtureRequest

from humbldata.toolbox.technical.mandelbrot_channel.helpers import (
    add_window_index,
)


# FIXTURES =====================================================================
@pytest.fixture(
    params=[
        "dataframe_single_symbol",
        "lazyframe_single_symbol",
        "dataframe_multiple_symbols",
        "lazyframe_multiple_symbols",
    ]
)
def equity_historical(request: type[FixtureRequest]):
    data = pl.read_csv(
        "tests\\toolbox\\custom_data\\equity_historical_multiple_1y.csv",
        try_parse_dates=True,
    )
    if request.param == "dataframe_single_symbol":
        data = data.filter(pl.col("symbol") == "AAPL")
        return data
    elif request.param == "lazyframe_single_symbol":
        data = data.filter(pl.col("symbol") == "AAPL")
        return pl.LazyFrame(data)
    elif request.param == "dataframe_multiple_symbols":
        return data
    elif request.param == "lazyframe_multiple_symbols":
        return pl.LazyFrame(data)
    return None


# add_window_index() TEST ======================================================


@pytest.mark.parametrize(
    ("window_str", "expected_count"),
    [
        # ("1d", 250),
        # ("1w", 52),
        ("1m", 12),
        ("3m", 4),
        ("6m", 2),
        ("1y", 1),
    ],
)
def test_add_window_index(
    equity_historical: pl.DataFrame | pl.LazyFrame | None,
    window_str,
    expected_count,
):
    """Test addition of `window_index` column on 1y of data"""
    index_data = add_window_index(equity_historical, window=window_str)

    if isinstance(index_data, pl.LazyFrame):
        index_data = index_data.collect()
    index_count = (
        index_data.select("window_index").unique().count().to_numpy()[0, 0]
    )
    assert index_count == expected_count


@pytest.fixture(
    params=[
        "dataframe_multiple_unequal_dates",
        "lazyframe_multiple_unequal_dates",
    ]
)
def equity_historical_edge_cases(request: type[FixtureRequest]):
    """Load equity historical data with unequal dates for testing edge cases."""
    data = pl.read_csv(
        "tests\\toolbox\\custom_data\\equity_historical_unequal_10y.csv",
        try_parse_dates=True,
    )
    if request.param == "dataframe_multiple_unequal_dates":
        return data
    elif request.param == "lazyframe_multiple_unequal_dates":
        return pl.LazyFrame(data)
    return None


# Define a dictionary mapping window_str to another dictionary of expected values for each stock
expected_values = {
    # "1d": {
    #     "AAPL": 2515,
    #     "PCT": 872,
    #     "SNAP": 1719,
    # },
    # "1w": {
    #     "AAPL": 521,
    #     "PCT": 180,
    #     "SNAP": 356,
    # },
    "1m": {
        "AAPL": 119,
        "PCT": 41,
        "SNAP": 81,
    },
    "3m": {
        "AAPL": 39,
        "PCT": 13,
        "SNAP": 27,
    },
    "6m": {
        "AAPL": 19,
        "PCT": 6,
        "SNAP": 13,
    },
    "1y": {
        "AAPL": 9,
        "PCT": 3,
        "SNAP": 6,
    },
}


@pytest.mark.parametrize(
    ("window_str", "expected_counts"),
    [
        (window_str, expected_values[window_str])
        for window_str in expected_values
    ],
)
def test_add_window_index_edge_cases(
    equity_historical_edge_cases: pl.DataFrame | pl.LazyFrame | None,
    window_str,
    expected_counts,
):
    """Test addition of `window_index` column on 10y of data with edge cases, with unequal stock data dates."""
    index_data = add_window_index(
        equity_historical_edge_cases, window=window_str
    )
    if isinstance(index_data, pl.LazyFrame):
        index_data = index_data.collect()
    # Extract `window_index` counts for AAPL, PCT, SNAP
    index_counts = (
        index_data.group_by(pl.col("symbol"))
        .agg(pl.max("window_index"))
        .sort("symbol")
    )
    # Iterate through the expected counts and check against the actual data
    for symbol, expected_count in expected_counts.items():
        actual_count = index_counts.filter(pl.col("symbol") == symbol)[
            "window_index"
        ].to_numpy()[0]
        assert (
            actual_count == expected_count
        ), f"Failed for {symbol} with window_str {window_str}"


# _vol_buckets_engine() TEST ================================================
