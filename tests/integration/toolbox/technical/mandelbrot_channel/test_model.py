import polars as pl
import pytest
from _pytest.fixtures import FixtureRequest

from humbldata.toolbox.technical.mandelbrot_channel.model import (
    calc_mandelbrot_channel,
    calc_mandelbrot_channel_historical,
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
        "tests\\unittests\\toolbox\\custom_data\\equity_historical_multiple_1y.csv",
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


@pytest.mark.integration()
def test_mandelbrot_channel_integration(
    equity_historical, request: FixtureRequest
):
    """Testing the composed function of `calc_mandelbrot_channel()`."""
    current_param = request.node.callspec.params.get("equity_historical")

    mandelbrot = calc_mandelbrot_channel(
        equity_historical,
        window="1m",
        rv_adjustment=True,
        _rv_method="std",
        _rv_grouped_mean=False,
        _rs_method="RS",
        _live_price=False,
    ).collect()

    if "multiple" in current_param:
        result_shape = mandelbrot.select("symbol").unique().shape

        symbols_top_and_bottom_mean = {
            "AMD": ("AMD", 136.6295, 150.7249),
            "AAPL": ("AAPL", 192.2322, 197.8368),
            "GOOGL": ("GOOGL", 135.1688, 141.503),
            "PCT": ("PCT", 0.5771, 6.3277),
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
        assert result_shape == (4, 1)
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
def test_mandelbrot_channel_historical_integration(
    equity_historical, request: FixtureRequest
):
    """Testing the composed function of `calc_mandelbrot_channel()`."""
    current_param = request.node.callspec.params.get("equity_historical")

    mandelbrot_historical = calc_mandelbrot_channel_historical(
        equity_historical,
        window="1m",
        rv_adjustment=True,
        _rv_method="std",
        _rv_grouped_mean=False,
        _rs_method="RS",
        _live_price=False,
    )

    if "multiple" in current_param:
        result_shape = mandelbrot_historical.select("symbol").unique().shape
        aapl_top_and_bottom_mean = (
            mandelbrot_historical.group_by("symbol")
            .agg(pl.col("bottom_price").mean(), pl.col("top_price").mean())
            .row(by_predicate=pl.col("symbol") == "AAPL")
        )
        expected_aapl_top_and_bottom = (
            "AAPL",
            pytest.approx(172.17, rel=1e-3),
            pytest.approx(179.53, rel=1e-3),
        )
        pct_top_and_bottom_mean = (
            mandelbrot_historical.group_by("symbol")
            .agg(pl.col("bottom_price").mean(), pl.col("top_price").mean())
            .row(by_predicate=pl.col("symbol") == "PCT")
        )
        expected_pct_top_and_bottom = (
            "PCT",
            pytest.approx(4.81, rel=1e-3),
            pytest.approx(9.26, rel=1e-3),
        )
        google_top_and_bottom_mean = (
            mandelbrot_historical.group_by("symbol")
            .agg(pl.col("bottom_price").mean(), pl.col("top_price").mean())
            .row(by_predicate=pl.col("symbol") == "GOOGL")
        )
        expected_google_top_and_bottom = (
            "GOOGL",
            pytest.approx(116.95, rel=1e-3),
            pytest.approx(125.30, rel=1e-3),
        )
        amd_top_and_bottom_mean = (
            mandelbrot_historical.group_by("symbol")
            .agg(pl.col("bottom_price").mean(), pl.col("top_price").mean())
            .row(by_predicate=pl.col("symbol") == "AMD")
        )
        expected_amd_top_and_bottom = (
            "AMD",
            pytest.approx(97.66, rel=1e-3),
            pytest.approx(115.28, rel=1e-3),
        )

        assert google_top_and_bottom_mean == expected_google_top_and_bottom
        assert amd_top_and_bottom_mean == expected_amd_top_and_bottom
        assert pct_top_and_bottom_mean == expected_pct_top_and_bottom
        assert aapl_top_and_bottom_mean == expected_aapl_top_and_bottom
        assert result_shape == (4, 1)
    else:
        result_shape = mandelbrot_historical.select("symbol").unique().shape
        aapl_top_and_bottom_mean = (
            mandelbrot_historical.group_by("symbol")
            .agg(pl.col("bottom_price").mean(), pl.col("top_price").mean())
            .row(by_predicate=pl.col("symbol") == "AAPL")
        )
        expected_aapl_top_and_bottom = (
            "AAPL",
            pytest.approx(172.17, rel=1e-3),
            pytest.approx(179.53, rel=1e-3),
        )

        assert aapl_top_and_bottom_mean == expected_aapl_top_and_bottom
        assert result_shape == (1, 1)
        assert mandelbrot_historical.columns == [
            "date",
            "symbol",
            "bottom_price",
            "close",
            "top_price",
        ]
