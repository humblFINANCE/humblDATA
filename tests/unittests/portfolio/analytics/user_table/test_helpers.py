from datetime import date, datetime, timedelta

import polars as pl
import pytest

from humbldata.core.standard_models.portfolio.analytics.etf_category import (
    ETFCategoryData,
)
from humbldata.portfolio.analytics.watchlist.helpers import (
    aget_asset_class_filter,
    aget_sector_filter,
    calc_up_down_pct,
)
from humbldata.toolbox.toolbox_controller import Toolbox


@pytest.fixture(params=["lazyframe", "dataframe"])
def price_data(request):
    """
    Fixture that provides sample price data in both LazyFrame and DataFrame formats.
    """
    data = {
        "symbol": ["AAPL", "GOOGL", "AMZN"],
        "recent_price": [150.0, 2800.0, 3000.0],
        "bottom_price": [120.0, 2700.0, 3100.0],
        "top_price": [160.0, 2900.0, 3400.0],
    }
    if request.param == "lazyframe":
        return pl.LazyFrame(data)
    else:
        return pl.DataFrame(data)


def test_calc_up_down_pct(price_data):
    """
    Test the calc_up_down_pct function with default column names.
    """
    result = calc_up_down_pct(price_data)

    if isinstance(result, pl.LazyFrame):
        result = result.collect()

    expected_ud_pct = ["-20.0 / +6.67", "-3.57 / +3.57", "-3.33 / +13.33"]
    expected_ud_ratio = [0.25, 0.5, 0.8]

    assert result["ud_pct"].to_list() == expected_ud_pct
    assert result["ud_ratio"].to_list() == expected_ud_ratio
    assert "recent_price" in result.columns
    assert "bottom_price" in result.columns
    assert "top_price" in result.columns


def test_calc_up_down_pct_custom_column_names(price_data):
    """
    Test the calc_up_down_pct function with custom column names.
    """
    result = calc_up_down_pct(
        price_data,
        recent_price_col="recent_price",
        bottom_price_col="bottom_price",
        top_price_col="top_price",
        pct_output_col="custom_ud_pct",
        ratio_output_col="custom_ud_ratio",
    )

    if isinstance(result, pl.LazyFrame):
        result = result.collect()

    assert "custom_ud_pct" in result.columns
    assert "custom_ud_ratio" in result.columns


@pytest.fixture(params=["lazyframe", "dataframe"])
def etf_data_samples(request):
    """
    Fixture that provides sample ETF data in both LazyFrame and DataFrame formats.
    """
    data = [
        {
            "symbol": ["AAPL", "XLE", "DBA"],
            "category": [None, "Equity Energy", "Commodities Focused"],
        },
        {
            "symbol": ["XLE", "XLK", "XLF"],
            "category": ["Equity Energy", "Technology", "Financial"],
        },
        {"symbol": ["AAPL", "NVDA", "TSLA"], "category": [None, None, None]},
        {
            "symbol": ["UUP", "UDN", "BITI", "ETHU", "LNGG"],
            "category": [
                "Trading--Miscellaneous",
                "Trading--Miscellaneous",
                "Trading--Miscellaneous",
                None,
                "Equity Energy",
            ],
        },
    ]

    if request.param == "lazyframe":
        return [pl.LazyFrame(sample).cast(pl.Utf8) for sample in data]
    else:
        return [pl.DataFrame(sample).cast(pl.Utf8) for sample in data]


@pytest.mark.asyncio()
async def test_aget_asset_class_filter(etf_data_samples):
    """
    Test the aget_asset_class_filter function with various ETF data samples.

    This function also inherently tests the `normalize_asset_class` function.
    """
    for sample in etf_data_samples:
        etf_data = ETFCategoryData(sample)
        symbols = sample.lazy().select("symbol").collect().to_series().to_list()

        result = await aget_asset_class_filter(symbols, etf_data=etf_data)
        result = (
            result.collect()
        )  # Convert LazyFrame to DataFrame for easier assertion

        assert "symbol" in result.columns
        assert "asset_class" in result.columns
        assert len(result) == len(symbols)

        # Check specific mappings
        for symbol, asset_class in zip(result["symbol"], result["asset_class"]):
            if symbol in ["AAPL", "NVDA", "TSLA"]:
                assert asset_class == "Equity"
            elif symbol == "XLE":
                assert asset_class == "Equity"
            elif symbol == "DBA":
                assert asset_class == "Commodity"
            elif symbol == "XLK":
                assert asset_class == "Equity"
            elif symbol == "XLF":
                assert asset_class == "Equity"
            elif symbol in ["UUP", "UDN"]:
                assert asset_class == "Cash"
            elif symbol in ["BITI", "ETHU"]:
                assert asset_class == "Crypto"
            elif symbol == "LNGG":
                assert asset_class == "Commodity"


@pytest.mark.asyncio()
async def test_aget_asset_class_filter_without_etf_data(mocker):
    """
    Test the aget_asset_class_filter function without providing ETF data.
    """
    symbols = ["AAPL", "XLE", "DBA"]
    mock_aget_etf_category = mocker.patch(
        "humbldata.portfolio.analytics.watchlist.helpers.aget_etf_category"
    )
    mock_aget_etf_category.return_value = pl.LazyFrame(
        {
            "symbol": symbols,
            "category": [None, "Equity Energy", "Commodities Focused"],
        }
    )

    result = await aget_asset_class_filter(symbols)
    result = result.collect()

    assert "symbol" in result.columns
    assert "asset_class" in result.columns
    assert len(result) == len(symbols)

    mock_aget_etf_category.assert_called_once_with(symbols, provider="yfinance")

    # Check specific mappings
    for symbol, asset_class in zip(result["symbol"], result["asset_class"]):
        if symbol == "AAPL":
            assert asset_class == "Equity"
        elif symbol == "XLE":
            assert asset_class == "Equity"
        elif symbol == "DBA":
            assert asset_class == "Commodity"


@pytest.fixture(params=["lazyframe", "dataframe"])
def equity_sector_data(request):
    equity_data = [
        pl.DataFrame(
            {
                "symbol": ["AAPL", "NVDA", "TSLA"],
                "sector": ["Technology", "Technology", "Consumer Cyclical"],
            }
        ),
        pl.DataFrame(
            {"symbol": ["XLE", "XLF", "XLU"], "sector": [None, None, None]}
        ),
        pl.DataFrame(
            {
                "symbol": ["AAPL", "XLE", "XLU", "TSLA"],
                "sector": ["Technology", None, None, "Consumer Cyclical"],
            }
        ),
        pl.DataFrame(
            {
                "symbol": ["BITI", "LNGG", "ETHU", "DBA"],
                "sector": [None, None, None, None],
            }
        ),
    ]

    etf_data = [
        pl.DataFrame(
            {"symbol": ["AAPL", "NVDA", "TSLA"], "category": [None, None, None]}
        ),
        pl.DataFrame(
            {
                "symbol": ["XLE", "XLF", "XLU"],
                "category": ["Equity Energy", "Financial", "Utilities"],
            }
        ),
        pl.DataFrame(
            {
                "symbol": ["AAPL", "XLE", "XLU", "TSLA"],
                "category": [None, "Equity Energy", "Utilities", None],
            }
        ),
        pl.DataFrame(
            {
                "symbol": ["BITI", "LNGG", "ETHU", "DBA"],
                "category": [
                    "Trading--Miscellaneous",
                    "Equity Energy",
                    None,
                    "Commodities Focused",
                ],
            }
        ),
    ]

    if request.param == "lazyframe":
        return [
            (df.lazy().cast(pl.Utf8), etf.lazy().cast(pl.Utf8))
            for df, etf in zip(equity_data, etf_data)
        ]
    else:
        return [
            (df.cast(pl.Utf8), etf.cast(pl.Utf8))
            for df, etf in zip(equity_data, etf_data)
        ]


@pytest.mark.asyncio()
async def test_aget_sector_filter(equity_sector_data, mocker):
    for equity_data, etf_data in equity_sector_data:
        symbols = (
            equity_data.lazy().select("symbol").collect().to_series().to_list()
        )

        mock_aget_equity_sector = mocker.patch(
            "humbldata.portfolio.analytics.watchlist.helpers.aget_equity_sector"
        )
        mock_aget_equity_sector.return_value = equity_data

        result = await aget_sector_filter(
            symbols, etf_data=ETFCategoryData(etf_data)
        )
        result = result.lazy().collect()

        # print(f"Input symbols: {symbols}")
        # print(f"Equity data:\n{equity_data}")
        # print(f"ETF data:\n{etf_data}")
        # print(f"Result:\n{result}")

        assert "symbol" in result.columns
        assert "sector" in result.columns
        assert len(result) == len(
            symbols
        ), f"Expected {len(symbols)} rows, but got {len(result)} rows"

        # Check specific mappings
        if len(symbols) == 3:
            if symbols[0] == "AAPL":
                expected = [
                    ("AAPL", "Technology"),
                    ("NVDA", "Technology"),
                    ("TSLA", "Consumer Cyclical"),
                ]
            else:
                expected = [
                    ("XLE", "Energy"),
                    ("XLF", "Financials"),
                    ("XLU", "Utilities"),
                ]
        elif len(symbols) == 4:
            if symbols[0] == "AAPL":
                expected = [
                    ("AAPL", "Technology"),
                    ("TSLA", "Consumer Cyclical"),
                    ("XLE", "Energy"),
                    ("XLU", "Utilities"),
                ]
            else:
                expected = [
                    ("BITI", "Trading--Miscellaneous"),
                    ("LNGG", "Energy"),
                    ("ETHU", None),
                    ("DBA", "Commodities Focused"),
                ]

        for (exp_symbol, exp_sector), (res_symbol, res_sector) in zip(
            expected, result.rows()
        ):
            assert (
                exp_symbol == res_symbol
            ), f"Expected symbol {exp_symbol}, but got {res_symbol}"
            assert (
                exp_sector == res_sector
            ), f"Expected sector {exp_sector} for {exp_symbol}, but got {res_sector}"

        mock_aget_equity_sector.assert_called_once_with(
            symbols, provider="yfinance"
        )
