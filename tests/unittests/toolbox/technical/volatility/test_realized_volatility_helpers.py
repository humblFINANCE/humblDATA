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
    data = pl.read_parquet("tests/test_data/test_data.parquet").filter(
        pl.col("symbol") == "AAPL"
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
        assert result == pytest.approx(0.47984450128973993, 0.01)


def test_std(volatility_test_df):
    if isinstance(volatility_test_df, pl.Series):
        result = std(volatility_test_df)
        assert len(result) == 6035
        assert result.sum() == pytest.approx(133.25, 0.01)

    else:
        result = std(
            volatility_test_df, _column_name_returns="log_returns"
        ).select(cs.contains("std"))

        if isinstance(result, pl.LazyFrame):
            result = result.collect()
            std_sum = result.to_series().sum()
            assert len(result) == 6034
            assert std_sum == pytest.approx(167.65, 0.01)
            assert result.to_series().mean() == pytest.approx(
                0.027784774856283986, 0.01
            )


def test_parkinson(volatility_test_df):
    if isinstance(volatility_test_df, pl.Series):
        pass
    else:
        result = (
            parkinson(volatility_test_df)
            .select(cs.contains("parkinson"))
            .collect()
        )

        assert len(result) == 6035
        assert result.to_series().sum() == pytest.approx(
            175743.71404752193, 0.01
        )
        assert result.to_series().mean() == pytest.approx(29.120, 0.01)


def test_garman_klass(volatility_test_df):
    if isinstance(volatility_test_df, pl.Series):
        pass
    else:
        result = (
            garman_klass(volatility_test_df).select(cs.contains("gk")).collect()
        )
        assert len(result) == 6035
        assert result.to_series().mean() == pytest.approx(29.21, 0.1)
        assert result.to_series().sum() == pytest.approx(176337.35, 0.01)


def test_hodges_tompkins(volatility_test_df):
    if isinstance(volatility_test_df, pl.Series):
        pass
    else:
        result = (
            hodges_tompkins(volatility_test_df)
            .select(cs.contains("ht"))
            .collect()
        )
        assert len(result) == 6034
        assert result.to_series().mean() == pytest.approx(34.81, 0.01)
        assert result.to_series().sum() == pytest.approx(210076.44, 0.01)


def test_rogers_satchell(volatility_test_df):
    if isinstance(volatility_test_df, pl.Series):
        pass
    else:
        result = (
            rogers_satchell(volatility_test_df, _column_name_close="close")
            .select(cs.contains("rs_volatility"))
            .collect()
        )

        assert len(result) == 6035
        assert result.to_series().mean() == pytest.approx(
            29.442, 0.01
        )  # Adjust the expected values as needed
        assert result.to_series().sum() == pytest.approx(
            177684.54, 0.01
        )  # Adjust the expected values as needed


def test_yang_zhang(volatility_test_df):
    if isinstance(volatility_test_df, pl.Series):
        pass
    else:
        result = (
            yang_zhang(volatility_test_df, _column_name_close="close")
            .select(cs.contains("yz_volatility"))
            .collect()
        )
        assert len(result) == 6034
        assert result.to_series().mean() == pytest.approx(
            37.64, 0.01
        )  # Adjust the expected values as needed based on yang_zhang results
        assert result.to_series().sum() == pytest.approx(
            227141.37, 0.01
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
        assert len(result) == 6035
        assert result.to_series().mean() == pytest.approx(
            6.62, 0.01
        )  # Adjust the expected values as needed based on yang_zhang results
        assert result.to_series().sum() == pytest.approx(
            39971.22, 0.01
        )  # Adjust the expected values as needed based on yang_zhang results
