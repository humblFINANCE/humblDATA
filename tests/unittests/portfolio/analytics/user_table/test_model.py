import polars as pl
import pytest

from humbldata.portfolio.analytics.watchlist.model import watchlist_table_engine
from humbldata.toolbox.toolbox_controller import Toolbox


@pytest.fixture()
def etf_data():
    return [
        pl.DataFrame(
            {"symbol": ["AAPL", "NVDA", "TSLA"], "category": [None, None, None]}
        ).cast(pl.String),
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


@pytest.fixture()
def mandelbrot_data():
    return [
        pl.DataFrame(
            {
                "date": ["2023-12-29"] * 3,
                "symbol": ["AAPL", "NVDA", "TSLA"],
                "bottom_price": [191.0565, 45.3305, 236.507],
                "recent_price": [192.024185, 49.51561, 248.479996],
                "top_price": [209.2658, 50.9743, 264.9378],
            }
        ),
        pl.DataFrame(
            {
                "date": ["2023-12-29"] * 3,
                "symbol": ["XLE", "XLF", "XLU"],
                "bottom_price": [76.726, 36.9742, 61.7343],
                "recent_price": [82.505325, 37.31123, 62.308685],
                "top_price": [86.0857, 38.421, 64.8154],
            }
        ),
        pl.DataFrame(
            {
                "date": ["2023-12-29"] * 4,
                "symbol": ["AAPL", "TSLA", "XLE", "XLU"],
                "bottom_price": [191.0565, 236.507, 80.0601, 61.7343],
                "recent_price": [192.024185, 248.479996, 82.505325, 62.308685],
                "top_price": [209.2658, 264.9378, 84.0202, 64.8154],
            }
        ),
        pl.DataFrame(
            {
                "date": ["2024-07-09"] * 4,
                "symbol": ["BITI", "DBA", "ETHU", "LNGG"],
                "bottom_price": [8.0322, 23.9992, 8.4655, 25.7606],
                "recent_price": [8.7, 24.360001, 9.59, 26.145],
                "top_price": [9.7926, 24.5792, 11.5106, 26.5588],
            }
        ),
    ]


@pytest.fixture()
def mock_latest_price(mocker):
    mock = mocker.patch(
        "humbldata.portfolio.analytics.watchlist.model.aget_latest_price"
    )
    mock.side_effect = [
        pl.DataFrame(
            {
                "symbol": ["AAPL", "NVDA", "TSLA"],
                "last_price": [228.68, 131.38, 262.33],
            }
        ),
        pl.DataFrame(
            {
                "symbol": ["XLE", "XLF", "XLU"],
                "last_price": [89.55, 41.43, 68.62],
            }
        ),
        pl.DataFrame(
            {
                "symbol": ["AAPL", "XLE", "XLU", "TSLA"],
                "last_price": [228.68, 89.55, 68.62, 262.33],
            }
        ),
        pl.DataFrame(
            {
                "symbol": ["BITI", "LNGG", "ETHU", "DBA"],
                "last_price": [8.91, 26.2427, 9.2, 24.01],
            }
        ),
    ]
    return mock


@pytest.fixture()
def mock_sector_filter(mocker):
    mock = mocker.patch(
        "humbldata.portfolio.analytics.watchlist.model.aget_sector_filter"
    )
    mock.side_effect = [
        pl.DataFrame(
            {
                "symbol": ["AAPL", "NVDA", "TSLA"],
                "sector": ["Technology", "Technology", "Consumer Cyclical"],
            }
        ),
        pl.DataFrame(
            {
                "symbol": ["XLE", "XLF", "XLU"],
                "sector": ["Energy", "Financials", "Utilities"],
            }
        ),
        pl.DataFrame(
            {
                "symbol": ["AAPL", "TSLA", "XLE", "XLU"],
                "sector": [
                    "Technology",
                    "Consumer Cyclical",
                    "Energy",
                    "Utilities",
                ],
            }
        ),
        pl.DataFrame(
            {
                "symbol": ["BITI", "LNGG", "ETHU", "DBA"],
                "sector": [
                    "Trading--Miscellaneous",
                    "Energy",
                    None,
                    "Commodities Focused",
                ],
            }
        ),
    ]
    return mock


@pytest.fixture()
def mock_asset_class_filter(mocker):
    mock = mocker.patch(
        "humbldata.portfolio.analytics.watchlist.model.aget_asset_class_filter"
    )
    mock.side_effect = [
        pl.DataFrame(
            {
                "symbol": ["AAPL", "NVDA", "TSLA"],
                "asset_class": ["Equity", "Equity", "Equity"],
            }
        ),
        pl.DataFrame(
            {
                "symbol": ["XLE", "XLF", "XLU"],
                "asset_class": ["Equity", "Equity", "Equity"],
            }
        ),
        pl.DataFrame(
            {
                "symbol": ["AAPL", "XLE", "XLU", "TSLA"],
                "asset_class": ["Equity", "Equity", "Equity", "Equity"],
            }
        ),
        pl.DataFrame(
            {
                "symbol": ["BITI", "LNGG", "ETHU", "DBA"],
                "asset_class": ["Crypto", "Commodity", "Crypto", "Commodity"],
            }
        ),
    ]
    return mock


@pytest.mark.asyncio()
@pytest.mark.parametrize(
    "symbols, etf_idx, mandelbrot_idx",
    [
        (["AAPL", "NVDA", "TSLA"], 0, 0),
        (["XLE", "XLF", "XLU"], 1, 1),
        (["AAPL", "XLE", "XLU", "TSLA"], 2, 2),
        (["BITI", "LNGG", "ETHU", "DBA"], 3, 3),
    ],
)
async def test_watchlist_table_engine(
    symbols,
    etf_idx,
    mandelbrot_idx,
    etf_data,
    mandelbrot_data,
    mocker,
):
    # Prepare input data
    etf_input = etf_data[etf_idx].lazy()
    mandelbrot_input = mandelbrot_data[mandelbrot_idx].lazy()

    # Mock Toolbox
    mock_toolbox = mocker.Mock(spec=Toolbox)
    mock_mandelbrot = mocker.Mock()
    mock_mandelbrot.to_polars.return_value = mandelbrot_input
    mock_toolbox.technical.humbl_channel.return_value = mock_mandelbrot

    # Mock the async functions
    mock_latest_price = mocker.patch(
        "humbldata.portfolio.analytics.watchlist.model.aget_latest_price",
        autospec=True,
    )
    mock_sector_filter = mocker.patch(
        "humbldata.portfolio.analytics.watchlist.model.aget_sector_filter",
        autospec=True,
    )
    mock_asset_class_filter = mocker.patch(
        "humbldata.portfolio.analytics.watchlist.model.aget_asset_class_filter",
        autospec=True,
    )

    # Set return values for mocked functions
    mock_latest_price.return_value = pl.DataFrame(
        {"symbol": symbols, "last_price": [100.0] * len(symbols)}
    ).lazy()
    mock_sector_filter.return_value = pl.DataFrame(
        {"symbol": symbols, "sector": ["Technology"] * len(symbols)}
    ).lazy()
    mock_asset_class_filter.return_value = pl.DataFrame(
        {"symbol": symbols, "asset_class": ["Equity"] * len(symbols)}
    ).lazy()

    # Run the function
    result = await watchlist_table_engine(
        symbols=symbols,
        etf_data=etf_input,
        toolbox=mock_toolbox,
        mandelbrot_data=mandelbrot_input,
        membership="anonymous",  # Fixed membership for unit tests
    )

    # Collect the result
    result_df = result.collect()

    # Assertions
    assert isinstance(result, pl.LazyFrame)
    assert set(result_df.columns) == {
        "date",
        "symbol",
        "buy_price",
        "last_price",
        "sell_price",
        "ud_pct",
        "ud_ratio",
        "sector",
        "asset_class",
    }
    assert len(result_df) == len(symbols)
    assert set(result_df["symbol"]) == set(symbols)

    # Check if the data from different sources are correctly joined

    for symbol in symbols:
        row = result_df.filter(pl.col("symbol") == symbol)
        assert not row["asset_class"].is_null().all()
        assert not row["last_price"].is_null().all()
        assert not row["buy_price"].is_null().all()
        assert not row["sell_price"].is_null().all()
        assert not row["ud_pct"].is_null().all()
        assert not row["ud_ratio"].is_null().all()

    # Verify that mocked functions were called
    mock_latest_price.assert_called_once()
    # assert mock_latest_price.call_args[1]["symbols"] == symbols
    mock_sector_filter.assert_called_once()
    # assert mock_sector_filter.call_args[1]["symbols"] == symbols
    # assert mock_sector_filter.call_args[1]["etf_data"].equals(etf_input)
    mock_asset_class_filter.assert_called_once()
    # assert mock_asset_class_filter.call_args[1]["symbols"] == symbols
    # assert mock_asset_class_filter.call_args[1]["etf_data"].equals(etf_input)


@pytest.mark.asyncio()
async def test_watchlist_table_engine_without_etf_data(
    etf_data,
    mandelbrot_data,
    mock_latest_price,
    mock_sector_filter,
    mock_asset_class_filter,
    mocker,
):
    symbols = ["AAPL", "NVDA", "TSLA"]

    # Mock aget_etf_category
    mock_aget_etf_category = mocker.patch(
        "humbldata.portfolio.analytics.watchlist.model.aget_etf_category"
    )
    mock_aget_etf_category.return_value = etf_data[0].lazy()

    # Mock Toolbox
    mock_toolbox = mocker.Mock(spec=Toolbox)
    mock_mandelbrot = mocker.Mock()
    mock_mandelbrot.to_polars.return_value = mandelbrot_data[0].lazy()
    mock_toolbox.technical.humbl_channel.return_value = mock_mandelbrot

    # Mock the async functions
    mock_latest_price.return_value = pl.DataFrame(
        {"symbol": symbols, "last_price": [100.0] * len(symbols)}
    ).lazy()
    mock_sector_filter.return_value = pl.DataFrame(
        {"symbol": symbols, "sector": ["Technology"] * len(symbols)}
    ).lazy()
    mock_asset_class_filter.return_value = pl.DataFrame(
        {"symbol": symbols, "asset_class": ["Equity"] * len(symbols)}
    ).lazy()

    # Run the function
    result = await watchlist_table_engine(
        symbols=symbols, toolbox=mock_toolbox, membership="anonymous"
    )

    # Collect the result
    result_df = result.collect()

    # Assertions
    assert isinstance(result, pl.LazyFrame)
    assert set(result_df.columns) == {
        "date",
        "symbol",
        "buy_price",
        "last_price",
        "sell_price",
        "ud_pct",
        "ud_ratio",
        "sector",
        "asset_class",
    }
    assert len(result_df) == len(symbols)
    assert set(result_df["symbol"]) == set(symbols)

    # # Verify that mocked functions were called
    # mock_aget_etf_category.assert_called_once()
    # mock_latest_price.assert_called_once()
    # mock_sector_filter.assert_called_once()
    # mock_asset_class_filter.assert_called_once()


@pytest.mark.asyncio()
async def test_watchlist_table_engine_without_toolbox(
    etf_data,
    mandelbrot_data,
    mock_latest_price,
    mock_sector_filter,
    mock_asset_class_filter,
    mocker,
):
    symbols = ["AAPL", "NVDA", "TSLA"]

    mock_toolbox = mocker.Mock(spec=Toolbox)
    mock_mandelbrot = mocker.Mock()
    mock_mandelbrot.to_polars.return_value = mandelbrot_data[0].lazy()
    mock_toolbox.technical.humbl_channel.return_value = mock_mandelbrot

    # Run the function
    result = await watchlist_table_engine(
        symbols=symbols, etf_data=etf_data[0].lazy(), membership="anonymous"
    )

    # Collect the result
    result_df = result.collect()

    # Assertions
    assert isinstance(result, pl.LazyFrame)
    assert set(result_df.columns) == {
        "date",
        "symbol",
        "buy_price",
        "last_price",
        "sell_price",
        "ud_pct",
        "ud_ratio",
        "sector",
        "asset_class",
    }
    assert len(result_df) == len(symbols)
    assert set(result_df["symbol"]) == set(symbols)

    # Verify that mocked functions were called
    mock_latest_price.assert_called_once_with(symbols=symbols)
    mock_sector_filter.assert_called_once()
    mock_asset_class_filter.assert_called_once()
