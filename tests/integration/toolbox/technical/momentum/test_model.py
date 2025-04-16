import polars as pl
import pytest
from _pytest.fixtures import FixtureRequest

from humbldata.toolbox.technical.humbl_momentum.model import calc_humbl_momentum


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
    data = pl.read_parquet(
        "tests/test_data/test_data.parquet",
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


@pytest.mark.integration()
def test_momentum_log_integration(equity_historical, request: FixtureRequest):
    """Test the momentum function with logarithmic ROC method."""
    current_param = request.node.callspec.params.get("equity_historical")

    result = calc_humbl_momentum(
        equity_historical, method="log", window="1d"
    ).collect()

    if "multiple" in current_param:
        result_shape = result.select("symbol").unique().shape
        assert result_shape == (5, 1)

        # Test AAPL momentum values
        aapl_momentum_mean = (
            result.filter(pl.col("symbol") == "AAPL")
            .select("momentum")
            .mean()[0, 0]
        )
        assert (
            pytest.approx(aapl_momentum_mean, rel=1e-3) == 0.0009114373611441688
        )
    else:
        result_shape = result.select("symbol").unique().shape
        assert result_shape == (1, 1)

        momentum_mean = result.select("momentum").mean()[0, 0]
        assert pytest.approx(momentum_mean, rel=1e-3) == 0.0009114373611441688

    assert "momentum" in result.columns


@pytest.mark.integration()
def test_momentum_simple_integration(
    equity_historical, request: FixtureRequest
):
    """Test the momentum function with simple ROC method."""
    current_param = request.node.callspec.params.get("equity_historical")

    result = calc_humbl_momentum(
        equity_historical, method="simple", window="1d"
    ).collect()

    if "multiple" in current_param:
        result_shape = result.select("symbol").unique().shape
        assert result_shape == (5, 1)

        # Test AAPL momentum values
        aapl_momentum_mean = (
            result.filter(pl.col("symbol") == "AAPL")
            .select("momentum")
            .mean()[0, 0]
        )
        assert (
            pytest.approx(aapl_momentum_mean, rel=1e-3) == 0.0012300530273114878
        )
    else:
        result_shape = result.select("symbol").unique().shape
        assert result_shape == (1, 1)

        momentum_mean = result.select("momentum").mean()[0, 0]
        assert pytest.approx(momentum_mean, rel=1e-3) == 0.0012300530273114878

    assert "momentum" in result.columns


@pytest.mark.integration()
def test_momentum_shift_integration(equity_historical, request: FixtureRequest):
    """Test the momentum function with shift method."""
    current_param = request.node.callspec.params.get("equity_historical")

    result = calc_humbl_momentum(
        equity_historical, method="shift", window="1d"
    ).collect()

    if "multiple" in current_param:
        result_shape = result.select("symbol").unique().shape
        assert result_shape == (5, 1)

        # Test AAPL momentum values
        aapl_signal_mean = (
            result.filter(pl.col("symbol") == "AAPL")
            .select("momentum_signal")
            .mean()[0, 0]
        )
        assert pytest.approx(aapl_signal_mean, rel=1e-3) == 0.5213788531653961
    else:
        result_shape = result.select("symbol").unique().shape
        assert result_shape == (1, 1)

        signal_mean = result.select("momentum_signal").mean()[0, 0]
        assert pytest.approx(signal_mean, rel=1e-3) == 0.5213788531653961

    assert all(col in result.columns for col in ["shifted", "momentum_signal"])
