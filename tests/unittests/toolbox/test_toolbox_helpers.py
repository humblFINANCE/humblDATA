from datetime import datetime
from typing import Literal

import polars as pl
import pytest
from _pytest.fixtures import FixtureRequest
from polars.dataframe.frame import DataFrame
from polars.lazyframe.frame import LazyFrame
from polars.series.series import Series

from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.toolbox.toolbox_helpers import (
    _check_required_columns,
    _cumsum_check,
    _set_over_cols,
    _set_sort_cols,
    _window_format,
    _window_format_monthly,
    cum_sum,
    detrend,
    log_returns,
    mean,
    range_,
    std,
)


# FIXTURES (data used in tests) ================================================
@pytest.fixture()
def equity_historical():
    """pl.DataFrame of 1y of AAPL, AMD, GOOGL, PCT, AMZN equity data."""
    return pl.read_parquet("tests/test_data/test_data.parquet")


# @pytest.fixture()
# def equity_historical_single_1y_window_index_3m_df():
#     """pl.DataFrame of 1y of AAPL data with 3m window index."""
#     return pl.read_csv(
#         "tests\\unittests\\toolbox\\custom_data\\equity_historical_single_1y_window_index_3m.csv"
#     )


@pytest.mark.parametrize(
    "window_string, expected_result",
    [
        ("2 weeks", "2w"),
        ("2 week", "2w"),
        ("2 wks", "2w"),
        ("2 wk", "2w"),
        ("2 w", "2w"),
        ("2w", "2w"),
        ("2wk", "2w"),
        ("2wks", "2w"),
        ("2week", "2w"),
        ("2weeks", "2w"),
        ("2m", "2mo"),
        ("2mo", "2mo"),
        ("2month", "2mo"),
        ("2months", "2mo"),
        ("2 months", "2mo"),
        ("2 years", "2y"),
        ("2 year", "2y"),
        ("2y", "2y"),
        ("2 days", "2d"),
        ("2 day", "2d"),
        ("2d", "2d"),
        ("2day", "2d"),
        ("2days", "2d"),
        ("2 quarters", "2q"),
        ("2 quarter", "2q"),
        ("2q", "2q"),
        ("2qtr", "2q"),
        ("2qtrs", "2q"),
    ],
)
def test_window_format(
    window_string: Literal[
        "2 weeks",
        "2 week",
        "2 wks",
        "2 wk",
        "2 w",
        "2w",
        "2wk",
        "2wks",
        "2week",
        "2weeks",
        "2m",
        "2mo",
        "2month",
        "2months",
        "2 months",
        "2 years",
        "2 year",
        "2y",
        "2 days",
        "2 day",
        "2d",
        "2day",
        "2days",
        "2 quarters",
        "2 quarter",
        "2q",
        "2qtr",
        "2qtrs",
    ],
    expected_result: Literal["2w", "2mo", "2y", "2d", "2q"],
):
    """
    Test the _window_format function with various inputs.

    This test ensures that the _window_format function correctly formats
    different representations of time ranges into a standardized format.
    It also checks that an appropriate error is raised for invalid inputs.

    Parameters
    ----------
    window_string : str
        The input string representing a time range in various formats.
    expected_result : str
        The expected standardized format output from the _window_format function.

    Raises
    ------
    HumblDataError
        If the input string does not conform to an expected format, ensuring
        that the function correctly identifies and handles invalid inputs.
    """
    assert (
        _window_format(window_string, _return_timedelta=False)
        == expected_result
    )
    with pytest.raises(HumblDataError):
        _window_format("2x")


@pytest.mark.parametrize(
    ("window_string", "expected_result", "expected_error"),
    [
        ("2mo", 2, None),
        ("3mo", 3, None),
        ("4mo", 4, None),
        ("5mo", 5, None),
        ("6mo", 6, None),
        ("7mo", 7, None),
        ("8mo", 8, None),
        ("9mo", 9, None),
        ("10mo", 10, None),
        ("11mo", 11, None),
        ("12mo", 12, None),
        ("1y", 12, None),
        ("2y", 24, None),
        ("1w", 0, None),
        ("10d", 0, None),
        ("10p", 0, HumblDataError),
        ("10x", 0, HumblDataError),
        ("10days", 0, HumblDataError),
        ("1month", 0, HumblDataError),
    ],
)
def test_window_format_monthly(window_string, expected_result, expected_error):
    """Test that the _window_format function correctly formats monthly time ranges."""
    if expected_error:
        with pytest.raises(HumblDataError):
            _window_format_monthly(window_string)
    else:
        formatted_result = _window_format_monthly(window_string)
        assert formatted_result == expected_result


@pytest.fixture(params=["dataframe", "series", "lazyframe"])
def cumsum_ending_in_zero(request: type[FixtureRequest]):
    data = {
        "date": [datetime(2023, 1, i + 1) for i in range(5)],
        "cumdev": [1, 2, 3, 4, 0],
        # "symbol": ["AAPL" for _ in range(5)],
        # "window_index": [1 for _ in range(5)],
    }
    if request.param == "dataframe":
        return pl.DataFrame(data)
    elif request.param == "series":
        return pl.Series(data["cumdev"])
    elif request.param == "lazyframe":
        return pl.LazyFrame(data)
    return None


@pytest.fixture(params=["dataframe", "series", "lazyframe"])
def cumsum_not_ending_in_zero(request: type[FixtureRequest]):
    data = {
        "date": [datetime(2023, 1, i + 1) for i in range(5)],
        "cumdev": [1, 2, 3, 4, 5],
        # "symbol": ["AAPL" for _ in range(5)],
        # "window_index": [1 for _ in range(5)],
    }
    if request.param == "dataframe":
        return pl.DataFrame(data)
    elif request.param == "series":
        return pl.Series(data["cumdev"])
    elif request.param == "lazyframe":
        return pl.LazyFrame(data)
    return None


def test_cumsum_check_ending_in_zero(
    cumsum_ending_in_zero: DataFrame | Series | LazyFrame | None,
):
    """Test if cumdev check correctly identifies sequences ending in zero."""
    assert _cumsum_check(cumsum_ending_in_zero, "cumdev") is True


def test_cumsum_check_not_ending_in_zero(
    cumsum_not_ending_in_zero: DataFrame | Series | LazyFrame | None,
):
    """Test if cumdev check raises error for sequences not ending in zero."""
    with pytest.raises(HumblDataError):
        _cumsum_check(cumsum_not_ending_in_zero, "cumdev")


def test_cum_sum(equity_historical):
    """
    Test the cum_sum function on one symbol with a 1m window index.

    This test tests the functionality of the cum_sum function when the _mandelbrot_usage
    parameter is set to False. This is a special case, as the function will not be able to
    check if the cumulative sum ends in zero, as it would for the Mandelbrot Channel calculation.
    """
    data = equity_historical.filter(pl.col("symbol") == "AAPL")

    result = cum_sum(
        data=data,
        _column_name="close",
        _mandelbrot_usage=False,
    )
    locked_value = result.select("cum_sum").unique().sum().row(0)[0]

    assert locked_value == pytest.approx(2290130.93, 0.01)


@pytest.mark.parametrize(
    (
        "data",
        "_detrend_col",
        "_detrend_value_col",
        "_sort",
        "expected_exception",
    ),
    [
        (
            pl.DataFrame(
                {
                    "log_returns": [0.1, 0.2, 0.3],
                    "window_mean": [0.15, 0.15, 0.15],
                }
            ),
            "log_returns",
            "window_mean",
            False,
            None,
        ),
        (
            pl.DataFrame(
                {
                    "symbol": ["AAPL", "AAPL", "AAPL"],
                    "date": [
                        datetime(2023, 1, 1),
                        datetime(2023, 1, 2),
                        datetime(2023, 1, 3),
                    ],
                    "log_returns": [0.1, 0.2, 0.3],
                }
            ),
            "log_returns",
            "nonexistent_column",
            False,
            HumblDataError,
        ),
        (
            pl.Series([0.1, 0.2, 0.3]),
            "log_returns",
            pl.Series([0.15, 0.15, 0.15]),
            False,
            None,
        ),
        (
            pl.Series([0.1, 0.2, 0.3]),
            "log_returns",
            "window_mean",
            False,
            HumblDataError,
        ),
    ],
)
def test_detrend(
    data, _detrend_col, _detrend_value_col, _sort, expected_exception
):
    """Test the detrend function with various inputs and expected outcomes."""
    if expected_exception:
        with pytest.raises(expected_exception):
            detrend(
                data=data,
                _detrend_col=_detrend_col,
                _detrend_value_col=_detrend_value_col,
                _sort=_sort,
            )
    else:
        result = detrend(
            data=data,
            _detrend_col=_detrend_col,
            _detrend_value_col=_detrend_value_col,
            _sort=_sort,
        )
        if isinstance(data, pl.DataFrame | pl.LazyFrame):
            assert "detrended_log_returns" in result.columns
        elif isinstance(data, pl.Series):
            assert pytest.approx(result.to_list(), abs=0.01) == [
                -0.05,
                0.05,
                0.15,
            ]


# range_() TEST ================================================================


def test_range_over_symbol(
    equity_historical,
    column_name: str = "close",
    sort: bool = True,
    expected_no_ranges: int = 1115,
):
    """Test the range_ function with various column names and sort options."""

    result = range_(
        data=equity_historical,
        _column_name=column_name,
        _sort=sort,
    )
    no_ranges = len(result.select(pl.col(f"{column_name}_range")).unique())
    assert (
        no_ranges == expected_no_ranges
    ), f"Expected 1115 ranges, but got: {no_ranges}"
    assert (
        pytest.approx(
            result.select(pl.col(f"{column_name}_range"))
            .unique()
            .sum()
            .row(0)[0],
            0.01,
        )
        == 5006.78
    )


def test_range_over_window_index(equity_historical, column_name: str = "close"):
    """Test the range_ function with various column names and sort options."""

    data = equity_historical.filter(pl.col("symbol") == "AAPL")

    result = range_(
        data=data,
        _column_name="close",
        _sort=True,
    )
    no_ranges = len(result.select(pl.col(f"{column_name}_range")).unique())
    assert no_ranges == 288, f"Expected 288 ranges, but got: {no_ranges}"
    assert (
        pytest.approx(
            result.select(pl.col(f"{column_name}_range"))
            .unique()
            .sum()
            .row(0)[0],
            0.01,
        )
        == 1093.06
    )


# std() TEST ================================================================


def test_std_over_symbol(
    equity_historical,
    column_name: str = "close",
):
    """
    Test the std function with various column names.

    There is no window_index column added to the dataframe, so the
    function should only calculate std over groups of symbols, of which there are 5.
    """
    data = equity_historical.drop("window_index")

    result = std(
        data=data,
        _column_name=column_name,
    )
    no_stds = len(result.select(pl.col("close_std")).unique())
    std_sum = result.select(pl.col("close_std")).unique().sum().row(0)[0]
    assert no_stds == 5
    assert (
        pytest.approx(std_sum, 0.01) == 178.63
    ), f"Expected std: 53.48, but got: {std_sum}"


def test_std_over_window_index(equity_historical):
    """Test the std function with a 1m window index."""

    data = equity_historical.filter(pl.col("symbol") == "AAPL")

    result = std(
        data=data,
        _column_name="close",
    )
    no_stds = len(result.select(pl.col("close_std")).unique())
    std_sum = result.select(pl.col("close_std")).unique().sum().row(0)[0]
    assert no_stds == 288
    assert (
        pytest.approx(std_sum, 0.01) == 315.95
    ), f"Expected std: 34.48, but got: {std_sum}"


# mean() TEST ================================================================
def test_mean_over_symbol(equity_historical):
    """Test the mean function with a 3m window index."""
    data = equity_historical.drop("window_index")
    result = mean(
        data=data,
        _column_name="close",
    )

    no_means = len(result.select("window_mean").unique())
    assert no_means == 5

    means_sum = result.select("window_mean").unique().sum().row(0)[0]

    assert (
        pytest.approx(means_sum, 0.01) == 150.61
    ), f"Expected mean: 686.57, but got: {means_sum}"


def test_mean_over_window_index(equity_historical):
    """Test the mean function with a 1m window index."""
    data = equity_historical.filter(pl.col("symbol") == "AAPL")

    result = mean(
        data=data,
        _column_name="close",
    )

    no_means = len(result.select("window_mean").unique())
    assert no_means == 288

    means_sum = result.select("window_mean").unique().sum().row(0)[0]

    assert (
        pytest.approx(means_sum, 0.01) == 9922.90
    ), f"Expected mean: 686.57, but got: {means_sum}"


# log_returns TEST ================================================================
@pytest.fixture(params=["dataframe", "series", "lazyframe"])
def log_return_data(request: FixtureRequest):
    data = {
        "date": [datetime(2023, 1, i + 1) for i in range(5)],
        "values": [1, 2, 3, 4, 5],
    }
    if request.param == "dataframe":
        return pl.DataFrame(data)
    elif request.param == "series":
        return pl.Series(data["values"])
    elif request.param == "lazyframe":
        return pl.LazyFrame(data)
    return None


@pytest.mark.parametrize(
    ("drop_nulls", "expected_error"),
    [
        (True, None),
        (False, None),
        (True, HumblDataError),
        (False, HumblDataError),
    ],
)
def test_log_returns(
    log_return_data: pl.DataFrame | pl.Series | pl.LazyFrame | None,
    drop_nulls: bool,
    expected_error: HumblDataError | None,
):
    """Test if log_returns correctly calculates log returns with and without dropping nulls."""
    result = log_returns(log_return_data, "values", _drop_nulls=drop_nulls)

    if isinstance(result, pl.Series):
        assert result.sum() == pytest.approx(1.60, 0.01)
    if isinstance(result, pl.LazyFrame):
        result = result.collect()
    if isinstance(result, pl.DataFrame):
        assert result.columns == ["date", "values", "log_returns"]
        if drop_nulls:
            assert len(result) == 4
        else:
            assert len(result) == 5

    if expected_error and isinstance(result, pl.DataFrame):
        with pytest.raises(expected_error):
            log_returns(
                log_return_data.drop("date"), "values", _drop_nulls=drop_nulls
            )


# _set_*_cols TEST =============================================================


def test_set_over_cols(log_return_data: pl.DataFrame | pl.LazyFrame):
    """Test if _set_over_cols correctly identifies present columns."""
    # pl.Series type not accepted by _set_over_cols
    if isinstance(log_return_data, pl.Series):
        pass
    else:
        expected_columns = ["values"]
        expected_columns2 = ["values", "date"]
        result = _set_over_cols(log_return_data, "values", "nonexistent_column")
        result2 = _set_over_cols(log_return_data, "values", "date")
        assert (
            result == expected_columns
        ), f"Expected {expected_columns}, got {result}"
        assert (
            result2 == expected_columns2
        ), f"Expected {expected_columns2}, got {result2}"


def test_set_sort_cols(log_return_data: pl.DataFrame | pl.LazyFrame):
    """Test if _set_over_cols correctly identifies present columns."""
    # pl.Series type not accepted by _set_over_cols
    if isinstance(log_return_data, pl.Series):
        pass
    else:
        expected_columns = ["values"]
        expected_columns2 = ["values", "date"]
        result = _set_sort_cols(log_return_data, "values", "nonexistent_column")
        result2 = _set_sort_cols(log_return_data, "values", "date")
        assert (
            result == expected_columns
        ), f"Expected {expected_columns}, got {result}"
        assert (
            result2 == expected_columns2
        ), f"Expected {expected_columns2}, got {result2}"


def test_check_required_cols(log_return_data: pl.DataFrame | pl.LazyFrame):
    """Test if _check_required_cols correctly identifies present columns."""
    if isinstance(log_return_data, pl.Series):
        pass
    else:
        result = _check_required_columns(log_return_data, "values")
        assert result == None, f"Expected  None, got {result}"

        result2 = _check_required_columns(log_return_data, "values", "date")
        assert result2 == None, f"Expected None, got {result2}"

        # Function raises an error if you check a column that doesn't exist
        with pytest.raises(HumblDataError):
            _check_required_columns(
                log_return_data, "values", "date", "required_col"
            )
