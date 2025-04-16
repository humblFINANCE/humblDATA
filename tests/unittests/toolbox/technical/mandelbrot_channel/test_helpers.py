import polars as pl
import pytest
from _pytest.fixtures import FixtureRequest

from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.toolbox.technical.humbl_channel.helpers import (
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
    """One year of equity data, AAPL, AMZN, GOOGL, AMD, PCT symbols."""
    data = pl.read_parquet("tests/test_data/test_data.parquet")
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
    """Data from `calc_humbl_channel()` right before last `price_range()`"""
    data = pl.read_parquet("tests/test_data/test_data_pre_price_range.parquet")
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
        ("1m", 288),
        ("3m", 96),
        ("6m", 48),
        ("1y", 24),
    ],
)
def test_add_window_index(
    equity_historical: pl.DataFrame | pl.LazyFrame | None,
    window_str,
    expected_count,
):
    """Test addition of `window_index` column on 1y of data"""

    data = equity_historical.drop("window_index")

    index_data = add_window_index(data, window=window_str)

    if isinstance(index_data, pl.LazyFrame):
        index_data = index_data.collect()
    index_count = (
        index_data.select("window_index").unique().count().to_numpy()[0, 0]
    )
    assert index_count == expected_count


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
        "AAPL": 287,
        "AMZN": 287,
        "AMD": 287,
        "PCT": 41,
        "GOOGL": 232,
    },
    "3m": {
        "AAPL": 95,
        "AMZN": 95,
        "AMD": 95,
        "PCT": 13,
        "GOOGL": 77,
    },
    "6m": {
        "AAPL": 47,
        "AMZN": 47,
        "AMD": 47,
        "PCT": 6,
        "GOOGL": 38,
    },
    "1y": {
        "AAPL": 23,
        "AMZN": 23,
        "AMD": 23,
        "PCT": 3,
        "GOOGL": 19,
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
    equity_historical: pl.DataFrame | pl.LazyFrame | None,
    window_str,
    expected_counts,
    request: FixtureRequest,
):
    """
    Test addition of `window_index` column on 10y of data with edge cases.

    The data has unequal dates for each symbol.
    """
    data = equity_historical.drop("window_index")

    index_data = add_window_index(data, window=window_str)
    if isinstance(index_data, pl.LazyFrame):
        index_data = index_data.collect()
    # Extract `window_index` counts for AAPL, AMZN, AMD, PCT, GOOGL
    index_counts = (
        index_data.group_by(pl.col("symbol"))
        .agg(pl.max("window_index"))
        .sort("symbol")
    )
    # Iterate through the expected counts and check against the actual data
    current_param = request.node.callspec.params.get("equity_historical")

    if "multiple" in current_param:
        for symbol, expected_count in expected_counts.items():
            actual_count = index_counts.filter(pl.col("symbol") == symbol)[
                "window_index"
            ].to_numpy()[0]
            assert (
                actual_count == expected_count
            ), f"Failed for {symbol} with window_str {window_str}"
    else:
        expected_count = expected_counts["AAPL"]
        actual_count = index_counts.filter(pl.col("symbol") == "AAPL")[
            "window_index"
        ].to_numpy()[0]
        assert (
            actual_count == expected_count
        ), f"Failed for AAPL with window_str {window_str}"


# vol_buckets TEST =============================================================


@pytest.mark.parametrize("_boundary_group_down", [False, True])
def test_vol_buckets(
    equity_historical: pl.DataFrame | pl.LazyFrame,
    request: FixtureRequest,
    *,
    _boundary_group_down: bool,
):
    """Test the `vol_buckets` function."""
    result = vol_buckets(
        equity_historical,
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
        .row(0)[0]
    )
    mid_bucket_count = (
        result.filter(pl.col("vol_bucket") == "mid")
        .select(pl.col("len"))
        .row(0)[0]
    )
    low_bucket_count = (
        result.filter(pl.col("vol_bucket") == "low")
        .select(pl.col("len"))
        .row(0)[0]
    )
    current_param = request.node.callspec.params.get("equity_historical")

    # Assert
    if not _boundary_group_down:
        expected_result_high = 4773 if "multiple" in current_param else 1207
        assert high_bucket_count == expected_result_high
        expected_result = 9541 if "multiple" in current_param else 2414
        assert mid_bucket_count == expected_result
        expected_result = 9543 if "multiple" in current_param else 2414
        assert low_bucket_count == expected_result
    else:
        expected_result_high = 4770 if "multiple" in current_param else 1207
        assert high_bucket_count == expected_result_high
        expected_result = 9541 if "multiple" in current_param else 2413
        assert mid_bucket_count == expected_result
        expected_result = 9546 if "multiple" in current_param else 2415
        assert low_bucket_count == expected_result


@pytest.mark.parametrize("_drop_col", ["symbol", "realized_volatility"])
def test_vol_buckets_error(
    equity_historical: pl.DataFrame | pl.LazyFrame,
    request: FixtureRequest,
    _drop_col: str,
):
    """Testing an error condition when necessary columns arent available."""
    equity_historical = equity_historical.drop(_drop_col)

    with pytest.raises(HumblDataError):
        vol_buckets(equity_historical)


# vol_filter TEST =============================================================
def test_vol_filter(
    equity_historical: pl.DataFrame | pl.LazyFrame,
    request: FixtureRequest,
):
    """Test the `vol_filter` function.

    Running the `vol_filter()` function on `equity_historical` (which has a
    `vol_bucket` column) with `vol_bucket` column results in a only a `mid`
    bucket for AAPL and only a low bucket for AMZN.
    """
    current_param = request.node.callspec.params.get("equity_historical")

    result = vol_filter(equity_historical)
    if isinstance(result, pl.LazyFrame):
        result = result.collect()

    if "multiple" in current_param:
        mid_bucket_filtered_count = (
            result.group_by("vol_bucket")
            .agg(pl.len())
            .filter(pl.col("vol_bucket") == "mid")
            .select(pl.col("len"))
            .row(0)[0]
        )
        low_bucket_filtered_count = (
            result.group_by("vol_bucket")
            .agg(pl.len())
            .filter(pl.col("vol_bucket") == "low")
            .select(pl.col("len"))
            .row(0)[0]
        )
        assert mid_bucket_filtered_count == 1706
        assert low_bucket_filtered_count == 5433
    else:
        low_bucket_filtered_count = (
            result.group_by("vol_bucket")
            .agg(pl.len())
            .filter(pl.col("vol_bucket") == "low")
            .select(pl.col("len"))
            .row(0)[0]
        )
        assert low_bucket_filtered_count == 1811


@pytest.mark.parametrize("_drop_col", ["symbol", "vol_bucket"])
def test_vol_filter_error(
    equity_historical: pl.DataFrame | pl.LazyFrame,
    request: FixtureRequest,
    _drop_col: str,
):
    """Testing an error condition when necessary columns arent available."""
    equity_historical = equity_historical.drop(_drop_col)

    with pytest.raises(HumblDataError):
        vol_filter(equity_historical)


# price_range() TEST =============================================================


def test_price_range_missing_rs_method(equity_historical):
    """Test the `price_range` function with missing `rs_method`."""
    with pytest.raises(HumblDataError):
        price_range(
            equity_historical,
            recent_price_data=None,
            rs_method="nonexistent",
        )


@pytest.mark.parametrize(
    "recent_price_data",
    [
        None,
        pl.LazyFrame(
            {
                "symbol": ["AAPL", "GOOGL", "AMD", "PCT", "AMZN"],
                "recent_price": [172.52, 138.445, 95.67, 23.45, 145.56],
            }
        ),
    ],
)
def test_price_range(
    equity_historical_mandelbrot_pre_price_range,
    recent_price_data,
    request: FixtureRequest,
):
    """Test the `price_range` function."""
    current_param = request.node.callspec.params.get(
        "equity_historical_mandelbrot_pre_price_range"
    )

    recent_price_param = request.node.callspec.params.get("recent_price_data")

    result = price_range(
        equity_historical_mandelbrot_pre_price_range,
        recent_price_data=recent_price_data,
        rs_method="RS",
    ).collect()

    if "multiple" in current_param:
        assert result.shape == (5, 5)
        if recent_price_param is None:
            assert result.select("bottom_price").row(0)[0] == 191.9886
            assert result.select("bottom_price").row(1)[0] == 136.0361
            assert result.select("top_price").row(0)[0] == 197.5595
            assert result.select("top_price").row(1)[0] == 150.9074
        else:
            assert result.select("bottom_price").row(0)[0] == 172.2544
            assert result.select("bottom_price").row(1)[0] == 88.2882
            assert result.select("top_price").row(0)[0] == 177.2526
            assert result.select("top_price").row(1)[0] == 97.9398
    else:
        assert result.shape == (1, 5)

    assert result.columns == [
        "date",
        "symbol",
        "bottom_price",
        "recent_price",
        "top_price",
    ]
