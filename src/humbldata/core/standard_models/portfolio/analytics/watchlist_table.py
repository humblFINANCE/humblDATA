"""
WatchlistTable Standard Model.

Context: Portfolio || Category: Analytics || Command: watchlist_table.

This module is used to define the QueryParams and Data model for the
WatchlistTable command.
"""

import asyncio
from typing import TypeVar

import pandera.polars as pa
import polars as pl
import uvloop
from pydantic import field_validator

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.portfolio import PortfolioQueryParams
from humbldata.core.utils.core_helpers import serialize_lazyframe_to_ipc
from humbldata.core.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from humbldata.core.utils.env import Env
from humbldata.core.utils.logger import log_start_end, setup_logger
from humbldata.core.utils.openbb_helpers import aget_etf_category
from humbldata.portfolio.analytics.watchlist.model import watchlist_table_engine
from humbldata.toolbox.toolbox_controller import Toolbox

env = Env()
Q = TypeVar("Q", bound=PortfolioQueryParams)
logger = setup_logger(
    "WatchlistTableFetcher",
    env.LOGGER_LEVEL,
)
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class WatchlistTableQueryParams(QueryParams):
    """
    QueryParams model for the WatchlistTable command, a Pydantic v2 model.

    Parameters
    ----------
    symbols : str | list[str] | set[str]
        The symbol or ticker of the stock(s). Can be a single symbol, a comma-separated string,
        or a list/set of symbols. Default is "AAPL".
        Examples: "AAPL", "AAPL,MSFT", ["AAPL", "MSFT"]
        All inputs will be converted to uppercase.

    Notes
    -----
    The `symbols` input will be processed to ensure all symbols are uppercase
    and properly formatted, regardless of the input format.
    """

    symbols: str | list[str] | set[str] = pa.Field(
        default="AAPL",
        title="Symbol",
        description=QUERY_DESCRIPTIONS.get("symbol", ""),
    )

    @field_validator("symbols", mode="before", check_fields=False)
    @classmethod
    def upper_symbol(cls, v: str | list[str] | set[str]) -> str | list[str]:
        """
        Convert the stock symbol to uppercase.

        Parameters
        ----------
        v : Union[str, List[str], Set[str]]
            The stock symbol or collection of symbols to be converted.

        Returns
        -------
        Union[str, List[str]]
            The uppercase stock symbol or a comma-separated string of uppercase
            symbols.
        """
        # Handle empty inputs
        if not v:
            return []
        # If v is a string, split it by commas into a list. Otherwise, ensure it's a list.
        v = v.split(",") if isinstance(v, str) else v

        # Trim whitespace and check if all elements in the list are strings
        if not all(isinstance(item.strip(), str) for item in v):
            msg = "Every element in `symbol` list must be a `str`"
            raise ValueError(msg)

        # Convert all elements to uppercase, trim whitespace, and join them with a comma
        return [symbol.strip().upper() for symbol in v]


class WatchlistTableData(Data):
    """
    Data model for the watchlist_table command, a Pandera.Polars Model.

    This Data model is used to validate data in the `.transform_data()` method of the `WatchlistTableFetcher` class.

    Attributes
    ----------
    symbol : pl.Utf8
        The stock symbol.
    last_price : pl.Float64
        The last known price of the stock.
    buy_price : pl.Float64
        The recommended buy price for the stock.
    sell_price : pl.Float64
        The recommended sell price for the stock.
    ud_pct : pl.Utf8
        The upside/downside percentage.
    ud_ratio : pl.Float64
        The upside/downside ratio.
    asset_class : pl.Utf8
        The asset class of the stock.
    sector : pl.Utf8
        The sector of the stock.
    humbl_suggestion : pl.Utf8 | None
        The suggestion provided by HUMBL.

    Methods
    -------
    None

    """

    symbol: pl.Utf8 = pa.Field(
        default=None,
        title="Symbol",
        description=DATA_DESCRIPTIONS.get("symbol", ""),
        alias="(symbols|symbol)",
        regex=True,
    )
    last_price: pl.Float64 = pa.Field(
        default=None,
        title="Last Price",
        description=DATA_DESCRIPTIONS.get("last_price", ""),
    )
    buy_price: pl.Float64 = pa.Field(
        default=None,
        title="Buy Price",
        description=DATA_DESCRIPTIONS.get("buy_price", ""),
    )
    sell_price: pl.Float64 = pa.Field(
        default=None,
        title="Sell Price",
        description=DATA_DESCRIPTIONS.get("sell_price", ""),
    )
    ud_pct: pl.Utf8 = pa.Field(
        default=None,
        title="Upside/Downside Percentage",
        description=DATA_DESCRIPTIONS.get("ud_pct", ""),
    )
    ud_ratio: pl.Float64 = pa.Field(
        default=None,
        title="Upside/Downside Ratio",
        description=DATA_DESCRIPTIONS.get("ud_ratio", ""),
    )
    asset_class: pl.Utf8 = pa.Field(
        default=None,
        title="Asset Class",
        description=DATA_DESCRIPTIONS.get("asset_class", ""),
    )
    sector: pl.Utf8 = pa.Field(
        default=None,
        title="Sector",
        description=DATA_DESCRIPTIONS.get("sector", ""),
        nullable=True,
    )
    humbl_suggestion: pl.Utf8 | None = pa.Field(
        default=None,
        title="humblSuggestion",
        description=QUERY_DESCRIPTIONS.get("humbl_suggestion", ""),
    )


class WatchlistTableFetcher:
    """
    Fetcher for the WatchlistTable command.

    Parameters
    ----------
    context_params : PortfolioQueryParams
        The context parameters for the Portfolio query.
    command_params : WatchlistTableQueryParams
        The command-specific parameters for the WatchlistTable query.

    Attributes
    ----------
    context_params : PortfolioQueryParams
        Stores the context parameters passed during initialization.
    command_params : WatchlistTableQueryParams
        Stores the command-specific parameters passed during initialization.
    data : pl.DataFrame
        The raw data extracted from the data provider, before transformation.

    Methods
    -------
    transform_query()
        Transform the command-specific parameters into a query.
    extract_data()
        Extracts the data from the provider and returns it as a Polars DataFrame.
    transform_data()
        Transforms the command-specific data according to the WatchlistTable logic.
    fetch_data()
        Execute TET Pattern.

    Returns
    -------
    HumblObject
        results : WatchlistTableData
            Serializable results.
        provider : Literal['fmp', 'intrinio', 'polygon', 'tiingo', 'yfinance']
            Provider name.
        warnings : Optional[List[Warning_]]
            List of warnings.
        chart : Optional[Chart]
            Chart object.
        context_params : PortfolioQueryParams
            Context-specific parameters.
        command_params : WatchlistTableQueryParams
            Command-specific parameters.
    """

    def __init__(
        self,
        context_params: PortfolioQueryParams,
        command_params: WatchlistTableQueryParams,
    ):
        """
        Initialize the WatchlistTableFetcher with context and command parameters.

        Parameters
        ----------
        context_params : PortfolioQueryParams
            The context parameters for the Portfolio query.
        command_params : WatchlistTableQueryParams
            The command-specific parameters for the WatchlistTable query.
        """
        self.context_params = context_params
        self.command_params = command_params

    def transform_query(self):
        """
        Transform the command-specific parameters into a query.

        If command_params is not provided, it initializes a default WatchlistTableQueryParams object.
        """
        if not self.command_params:
            self.command_params = WatchlistTableQueryParams()
        else:
            self.command_params = WatchlistTableQueryParams(
                **self.command_params  # type: ignore  # noqa: PGH003
            )

    async def extract_data(self):
        """
        Extract the data from the provider and returns it as a Polars DataFrame.

        Returns
        -------
        pl.DataFrame
            The extracted data as a Polars DataFrame.

        """
        self.etf_data = await aget_etf_category(self.context_params.symbols)

        # Dates are automatically selected based on membership
        self.toolbox = Toolbox(
            symbols=self.context_params.symbols,
            membership=self.context_params.membership,
            interval="1d",
        )
        self.humbl_channel = await self.toolbox.technical.humbl_channel()
        self.humbl_channel = self.humbl_channel.to_polars(collect=False)
        return self

    async def transform_data(self):
        """
        Transform the command-specific data according to the watchlist_table logic.

        Returns
        -------
        pl.DataFrame
            The transformed data as a Polars DataFrame
        """
        # Implement data transformation logic here
        transformed_data: pl.LazyFrame = await watchlist_table_engine(
            symbols=self.context_params.symbols,
            etf_data=self.etf_data,
            humbl_channel_data=self.humbl_channel,  # type: ignore  # noqa: PGH003
            toolbox=self.toolbox,
        )
        self.transformed_data = WatchlistTableData(
            transformed_data.collect()
        ).lazy()  # type: ignore  # noqa: PGH003
        self.transformed_data = self.transformed_data.with_columns(
            pl.col(pl.Float64).round(2)
        )
        self.transformed_data = serialize_lazyframe_to_ipc(
            self.transformed_data
        )

        return self

    @log_start_end(logger=logger)
    async def fetch_data(self):
        """
        Execute TET Pattern.

        This method executes the query transformation, data fetching and
        transformation process by first calling `transform_query` to prepare the query parameters, then
        extracting the raw data using `extract_data` method, and finally
        transforming the raw data using `transform_data` method.

        Returns
        -------
        HumblObject
            The HumblObject containing the transformed data and metadata.
        """
        logger.debug("Running .transform_query()")
        self.transform_query()
        logger.debug("Running .extract_data()")
        await self.extract_data()
        logger.debug("Running .transform_data()")
        await self.transform_data()

        return HumblObject(
            results=self.transformed_data,
            provider=self.context_params.provider,
            warnings=None,
            chart=None,
            context_params=self.context_params,
            command_params=self.command_params,
        )
