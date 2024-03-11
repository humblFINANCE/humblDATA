import polars as pl
import pytest
from _pytest.fixtures import FixtureRequest

from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.toolbox.technical.mandelbrot_channel.helpers import (
    add_window_index,
    price_range,
    vol_buckets,
    vol_filter,
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
def equity_historical(request: FixtureRequest):
    """One year of equity data, AAPL & AMZN symbols."""
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


@pytest.fixture(
    params=[
        "dataframe_single_symbol",
        "lazyframe_single_symbol",
        "dataframe_multiple_symbols",
        "lazyframe_multiple_symbols",
    ]
)
def equity_historical_rv(request: FixtureRequest):
    """One year of equity data, AAPL & AMZN symbols & `realized_volatiliity` column."""
    data = pl.read_csv(
        "tests\\toolbox\\custom_data\\equity_historical_multiple_rv_1m.csv",
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


@pytest.fixture(
    params=[
        "dataframe_single_symbol",
        "lazyframe_single_symbol",
        "dataframe_multiple_symbols",
        "lazyframe_multiple_symbols",
    ]
)
def equity_historical_rv_volb(request: FixtureRequest):
    """One year of equity data, AAPL & AMZN symbols & `realized_volatiliity` + `vol_bucket` columns."""
    data = pl.read_csv(
        "tests\\toolbox\\custom_data\\equity_historical_multiple_rv_volb_1m.csv",
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


@pytest.fixture(
    params=[
        "dataframe_single_symbol",
        "lazyframe_single_symbol",
        "dataframe_multiple_symbols",
        "lazyframe_multiple_symbols",
    ]
)
def equity_historical_mandelbrot_pre_price_range(request: FixtureRequest):
    """1 month of data, ran through `calc_mandelbrot_channel()`"""
    data = pl.read_csv(
        "tests\\toolbox\\custom_data\\equity_historical_mandelbrot_pre_price_range_1m.csv",
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
    # Function doesnt support `d` and `w`
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


# vol_buckets TEST =============================================================


@pytest.mark.parametrize("_boundary_group_down", [False, True])
def test_vol_buckets(
    equity_historical_rv: pl.DataFrame | pl.LazyFrame,
    request: FixtureRequest,
    *,
    _boundary_group_down: bool,
):
    """Test the `vol_buckets` function."""
    result = vol_buckets(
        equity_historical_rv,
        lo_quantile=0.4,
        hi_quantile=0.8,
        _column_name_volatility="realized_volatility",
        _boundary_group_down=_boundary_group_down,
    )

    # Collect result for Assert
    if isinstance(result, pl.LazyFrame):
        result = result.collect()
    result = result.group_by("vol_bucket").agg(pl.len())
    high_bucket_count = (
        result.filter(pl.col("vol_bucket") == "high")
        .select(pl.col("len"))
        .to_series()[0]
    )
    mid_bucket_count = (
        result.filter(pl.col("vol_bucket") == "mid")
        .select(pl.col("len"))
        .to_series()[0]
    )
    low_bucket_count = (
        result.filter(pl.col("vol_bucket") == "low")
        .select(pl.col("len"))
        .to_series()[0]
    )
    current_param = request.node.callspec.params.get("equity_historical_rv")

    # Assert
    if not _boundary_group_down:
        expected_result_high = 9 if "multiple" in current_param else 4
        assert high_bucket_count == expected_result_high
        expected_result = 16 if "multiple" in current_param else 8
        assert mid_bucket_count == expected_result
        expected_result = 17 if "multiple" in current_param else 8
        assert low_bucket_count == expected_result
    else:
        expected_result_high = 8 if "multiple" in current_param else 4
        assert high_bucket_count == expected_result_high
        expected_result = 16 if "multiple" in current_param else 7
        assert mid_bucket_count == expected_result
        expected_result = 18 if "multiple" in current_param else 9
        assert low_bucket_count == expected_result


@pytest.mark.parametrize("_drop_col", ["symbol", "realized_volatility"])
def test_vol_buckets_error(
    equity_historical_rv: pl.DataFrame | pl.LazyFrame,
    request: FixtureRequest,
    _drop_col: str,
):
    """Testing an error condition when necessary columns arent available."""
    equity_historical_rv = equity_historical_rv.drop(_drop_col)

    with pytest.raises(HumblDataError):
        vol_buckets(equity_historical_rv)


# vol_filter TEST =============================================================
def test_vol_filter(
    equity_historical_rv_volb: pl.DataFrame | pl.LazyFrame,
    request: FixtureRequest,
):
    """Test the `vol_filter` function.

    Running the `vol_filter()` function on `equity_historical_rv_volb` with
    `vol_bucket` column results in a only a `mid` bucket for AAPL and only
    a low bucket for AMZN.
    """
    current_param = request.node.callspec.params.get(
        "equity_historical_rv_volb"
    )

    result = vol_filter(equity_historical_rv_volb)
    if isinstance(result, pl.LazyFrame):
        result = result.collect()

    if "multiple" in current_param:
        mid_bucket_filtered_count = (
            result.group_by("vol_bucket")
            .agg(pl.len())
            .filter(pl.col("vol_bucket") == "mid")
            .select(pl.col("len"))
            .to_series()[0]
        )
        low_bucket_filtered_count = (
            result.group_by("vol_bucket")
            .agg(pl.len())
            .filter(pl.col("vol_bucket") == "low")
            .select(pl.col("len"))
            .to_series()[0]
        )
        assert mid_bucket_filtered_count == 8
        assert low_bucket_filtered_count == 9
    else:
        mid_bucket_filtered_count = (
            result.group_by("vol_bucket")
            .agg(pl.len())
            .filter(pl.col("vol_bucket") == "mid")
            .select(pl.col("len"))
            .to_series()[0]
        )
        assert mid_bucket_filtered_count == 8


@pytest.mark.parametrize("_drop_col", ["symbol", "vol_bucket"])
def test_vol_filter_error(
    equity_historical_rv_volb: pl.DataFrame | pl.LazyFrame,
    request: FixtureRequest,
    _drop_col: str,
):
    """Testing an error condition when necessary columns arent available."""
    equity_historical_rv_volb = equity_historical_rv_volb.drop(_drop_col)

    with pytest.raises(HumblDataError):
        vol_filter(equity_historical_rv_volb)


# price_range TEST =============================================================


def test_price_range_missing_rs_method():
    """Test the `price_range` function with missing `rs_method`."""
    with pytest.raises(HumblDataError):
        price_range(
            equity_historical,
            recent_price_data=None,
            rs_method="nonexistent",
        )
