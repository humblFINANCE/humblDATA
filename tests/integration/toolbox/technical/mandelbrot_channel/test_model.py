import polars as pl
import pytest
from _pytest.fixtures import FixtureRequest

from humbldata.toolbox.technical.humbl_channel.model import (
    calc_humbl_channel,
    calc_humbl_channel_historical,
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
def test_humbl_channel_integration(equity_historical, request: FixtureRequest):
    """Testing the composed function of `calc_humbl_channel()`."""
    current_param = request.node.callspec.params.get("equity_historical")

    mandelbrot = calc_humbl_channel(
        equity_historical,
        window="1m",
        rv_adjustment=True,
        rv_method="std",
        rv_grouped_mean=False,
        rs_method="RS",
        live_price=False,
    ).collect()

    if "multiple" in current_param:
        result_shape = mandelbrot.select("symbol").unique().shape

        symbols_top_and_bottom_mean = {
            "AMD": ("AMD", 131.45, 152.31),
            "AAPL": ("AAPL", 191.06, 214.03),
            "GOOGL": ("GOOGL", 135.11, 141.29),
            "PCT": ("PCT", 2.41, 5.13),
            "AMZN": ("AMZN", 146.35, 159.35),
        }

        for symbol, (
            expected_symbol,
            expected_bottom,
            expected_top,
        ) in symbols_top_and_bottom_mean.items():
            symbol_top_and_bottom_mean = (
                mandelbrot.group_by("symbol")
                .agg(pl.col("bottom_price").mean(), pl.col("top_price").mean())
                .row(by_predicate=pl.col("symbol") == symbol)
            )
            expected_symbol_top_and_bottom = (
                expected_symbol,
                pytest.approx(expected_bottom, rel=1e-3),
                pytest.approx(expected_top, rel=1e-3),
            )
            assert symbol_top_and_bottom_mean == expected_symbol_top_and_bottom
        assert result_shape == (5, 1)
    else:
        result_shape = mandelbrot.select("symbol").unique().shape
        assert result_shape == (1, 1)

    assert mandelbrot.columns == [
        "date",
        "symbol",
        "bottom_price",
        "recent_price",
        "top_price",
    ]


@pytest.mark.integration()
def test_humbl_channel_historical_integration(
    equity_historical, request: FixtureRequest
):
    """Testing the composed function of `calc_humbl_channel()`."""
    current_param = request.node.callspec.params.get("equity_historical")

    mandelbrot_historical = calc_humbl_channel_historical(
        equity_historical,
        window="1m",
        rv_adjustment=True,
        rv_method="std",
        rv_grouped_mean=False,
        rs_method="RS",
        live_price=False,
    ).collect()

    if "multiple" in current_param:
        result_shape = mandelbrot_historical.select("symbol").unique().shape
        aapl_top_and_bottom_mean = (
            mandelbrot_historical.group_by("symbol")
            .agg(pl.col("bottom_price").mean(), pl.col("top_price").mean())
            .row(by_predicate=pl.col("symbol") == "AAPL")
        )
        expected_aapl_top_and_bottom = (
            "AAPL",
            pytest.approx(32.17, rel=1e-3),
            pytest.approx(36.96, rel=1e-3),
        )
        pct_top_and_bottom_mean = (
            mandelbrot_historical.group_by("symbol")
            .agg(pl.col("bottom_price").mean(), pl.col("top_price").mean())
            .row(by_predicate=pl.col("symbol") == "PCT")
        )
        expected_pct_top_and_bottom = (
            "PCT",
            pytest.approx(9.55, rel=1e-3),
            pytest.approx(12.00, rel=1e-3),
        )
        google_top_and_bottom_mean = (
            mandelbrot_historical.group_by("symbol")
            .agg(pl.col("bottom_price").mean(), pl.col("top_price").mean())
            .row(by_predicate=pl.col("symbol") == "GOOGL")
        )
        expected_google_top_and_bottom = (
            "GOOGL",
            pytest.approx(40.72, rel=1e-3),
            pytest.approx(43.00, rel=1e-3),
        )
        amd_top_and_bottom_mean = (
            mandelbrot_historical.group_by("symbol")
            .agg(pl.col("bottom_price").mean(), pl.col("top_price").mean())
            .row(by_predicate=pl.col("symbol") == "AMD")
        )
        expected_amd_top_and_bottom = (
            "AMD",
            pytest.approx(23.65, rel=1e-3),
            pytest.approx(27.26, rel=1e-3),
        )

        assert google_top_and_bottom_mean == expected_google_top_and_bottom
        assert amd_top_and_bottom_mean == expected_amd_top_and_bottom
        assert pct_top_and_bottom_mean == expected_pct_top_and_bottom
        assert aapl_top_and_bottom_mean == expected_aapl_top_and_bottom
        assert result_shape == (5, 1)
    else:
        result_shape = mandelbrot_historical.select("symbol").unique().shape
        aapl_top_and_bottom_mean = (
            mandelbrot_historical.group_by("symbol")
            .agg(pl.col("bottom_price").mean(), pl.col("top_price").mean())
            .row(by_predicate=pl.col("symbol") == "AAPL")
        )
        expected_aapl_top_and_bottom = (
            "AAPL",
            pytest.approx(33.43, rel=1e-3),
            pytest.approx(35.75, rel=1e-3),
        )

        assert aapl_top_and_bottom_mean == expected_aapl_top_and_bottom
        assert result_shape == (1, 1)
        assert mandelbrot_historical.columns == [
            "date",
            "symbol",
            "bottom_price",
            "close_price",
            "top_price",
        ]
