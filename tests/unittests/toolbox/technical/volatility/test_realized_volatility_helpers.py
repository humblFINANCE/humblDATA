import polars as pl
import polars.selectors as cs
import pytest
from _pytest.fixtures import FixtureRequest

from humbldata.toolbox.technical.volatility.realized_volatility_helpers import (
    _annual_vol,
    garman_klass,
    hodges_tompkins,
    parkinson,
    rogers_satchell,
    squared_returns,
    std,
    yang_zhang,
)


@pytest.fixture(params=["dataframe", "series", "lazyframe"])
def volatility_test_df(request: FixtureRequest):
    data = pl.read_csv(
        "tests\\unittests\\toolbox\\custom_data\\equity_historical_single_log_returns.csv",
        try_parse_dates=True,
    )
    if request.param == "dataframe":
        return data
    elif request.param == "series":
        return data.select("log_returns").to_series()
    elif request.param == "lazyframe":
        return data.lazy()
    return None


def test_annual_vol(volatility_test_df):
    if isinstance(volatility_test_df, pl.Series):
        result = _annual_vol(volatility_test_df, 252)
        assert result == pytest.approx(1.49, 0.01)


def test_std(volatility_test_df):
    if isinstance(volatility_test_df, pl.Series):
        result = std(volatility_test_df)
        assert len(result) == 5
        assert result.sum() == pytest.approx(0.0748, 0.01)

    else:
        result = std(
            volatility_test_df, _column_name_returns="log_returns"
        ).select(cs.contains("std"))

        if isinstance(result, pl.LazyFrame):
            result = result.collect()
            std_sum = result.to_series().sum()
            assert len(result) == 4
            assert std_sum == pytest.approx(118.84, 0.01)
            assert result.to_series().mean() == pytest.approx(29.71, 0.01)


def test_parkinson(volatility_test_df):
    if isinstance(volatility_test_df, pl.Series):
        pass
    else:
        result = (
            parkinson(volatility_test_df)
            .select(cs.contains("parkinson"))
            .collect()
        )

        assert len(result) == 5
        assert result.to_series().sum() == pytest.approx(140.85, 0.01)
        assert result.to_series().mean() == pytest.approx(28.17, 0.01)


def test_garman_klass(volatility_test_df):
    if isinstance(volatility_test_df, pl.Series):
        pass
    else:
        result = (
            garman_klass(volatility_test_df).select(cs.contains("gk")).collect()
        )
        assert len(result) == 5
        assert result.to_series().mean() == pytest.approx(28.76, 0.01)
        assert result.to_series().sum() == pytest.approx(143.81, 0.01)


def test_hodges_tompkins(volatility_test_df):
    if isinstance(volatility_test_df, pl.Series):
        pass
    else:
        result = (
            hodges_tompkins(volatility_test_df)
            .select(cs.contains("ht"))
            .collect()
        )
        assert len(result) == 4
        assert result.to_series().mean() == pytest.approx(10.64, 0.01)
        assert result.to_series().sum() == pytest.approx(42.59, 0.01)


def test_rogers_satchell(volatility_test_df):
    if isinstance(volatility_test_df, pl.Series):
        pass
    else:
        result = (
            rogers_satchell(volatility_test_df)
            .select(cs.contains("rs_volatility"))
            .collect()
        )

        assert len(result) == 5
        assert result.to_series().mean() == pytest.approx(
            30.41, 0.01
        )  # Adjust the expected values as needed
        assert result.to_series().sum() == pytest.approx(
            152.07, 0.01
        )  # Adjust the expected values as needed


def test_yang_zhang(volatility_test_df):
    if isinstance(volatility_test_df, pl.Series):
        pass
    else:
        result = (
            yang_zhang(volatility_test_df)
            .select(cs.contains("yz_volatility"))
            .collect()
        )
        assert len(result) == 4
        assert result.to_series().mean() == pytest.approx(
            12.18, 0.01
        )  # Adjust the expected values as needed based on yang_zhang results
        assert result.to_series().sum() == pytest.approx(
            48.73, 0.01
        )  # Adjust the expected values as needed based on yang_zhang results


def test_squared_returns(volatility_test_df):
    if isinstance(volatility_test_df, pl.Series):
        pass
    else:
        result = (
            squared_returns(volatility_test_df)
            .select(cs.contains("sq"))
            .collect()
        )
        assert len(result) == 5
        assert result.to_series().mean() == pytest.approx(
            2.84, 0.01
        )  # Adjust the expected values as needed based on yang_zhang results
        assert result.to_series().sum() == pytest.approx(
            14.20, 0.01
        )  # Adjust the expected values as needed based on yang_zhang results
