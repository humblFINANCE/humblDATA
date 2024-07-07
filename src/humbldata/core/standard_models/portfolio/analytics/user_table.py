"""
UserTable Standard Model.

Context: Portfolio || Category: Analytics || Command: user_table.

This module is used to define the QueryParams and Data model for the
UserTable command.
"""

from typing import Literal, TypeVar

import pandera.polars as pa
import polars as pl
from pydantic import Field, field_validator

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.portfolio import PortfolioQueryParams
from humbldata.core.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from humbldata.core.utils.openbb_helpers import aget_etf_category
from humbldata.portfolio.analytics.user_table.helpers import (
    aggregate_user_table_data,
    generate_user_table_toolbox,
)

Q = TypeVar("Q", bound=PortfolioQueryParams)


class UserTableQueryParams(QueryParams):
    """
    QueryParams model for the UserTable command, a Pydantic v2 model.

    Parameters
    ----------
    symbols : str | list[str] | set[str]
        The symbol or ticker of the stock(s). Can be a single symbol, a comma-separated string,
        or a list/set of symbols. Default is "AAPL".
        Examples: "AAPL", "AAPL,MSFT", ["AAPL", "MSFT"]
        All inputs will be converted to uppercase.

    user_role : Literal["peon", "premium", "power", "permanent", "admin"]
        The role of the user accessing the data. Default is "peon".

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
    user_role: Literal["peon", "premium", "power", "permanent", "admin"] = (
        Field(
            default="peon",
            title="User Role",
            description=QUERY_DESCRIPTIONS.get("user_role", ""),
        )
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
        # If v is a string, split it by commas into a list. Otherwise, ensure it's a list.
        v = v.split(",") if isinstance(v, str) else v

        # Trim whitespace and check if all elements in the list are strings
        if not all(isinstance(item.strip(), str) for item in v):
            msg = "Every element in `symbol` list must be a `str`"
            raise ValueError(msg)

        # Convert all elements to uppercase, trim whitespace, and join them with a comma
        return [symbol.strip().upper() for symbol in v]


class UserTableData(Data):
    """
    Data model for the user_table command, a Pandera.Polars Model.

    This Data model is used to validate data in the `.transform_data()` method of the `UserTableFetcher` class.
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
    )
    humbl_suggestion: pl.Utf8 | None = pa.Field(
        default=None,
        title="humblSuggestion",
        description=QUERY_DESCRIPTIONS.get("humbl_suggestion", ""),
    )


class UserTableFetcher:
    """
    Fetcher for the UserTable command.

    Parameters
    ----------
    context_params : PortfolioQueryParams
        The context parameters for the Portfolio query.
    command_params : UserTableQueryParams
        The command-specific parameters for the UserTable query.

    Attributes
    ----------
    context_params : PortfolioQueryParams
        Stores the context parameters passed during initialization.
    command_params : UserTableQueryParams
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
        Transforms the command-specific data according to the UserTable logic.
    fetch_data()
        Execute TET Pattern.

    Returns
    -------
    HumblObject
        results : UserTableData
            Serializable results.
        provider : Literal['fmp', 'intrinio', 'polygon', 'tiingo', 'yfinance']
            Provider name.
        warnings : Optional[List[Warning_]]
            List of warnings.
        chart : Optional[Chart]
            Chart object.
        context_params : PortfolioQueryParams
            Context-specific parameters.
        command_params : UserTableQueryParams
            Command-specific parameters.
    """

    def __init__(
        self,
        context_params: PortfolioQueryParams,
        command_params: UserTableQueryParams,
    ):
        """
        Initialize the UserTableFetcher with context and command parameters.

        Parameters
        ----------
        context_params : PortfolioQueryParams
            The context parameters for the Portfolio query.
        command_params : UserTableQueryParams
            The command-specific parameters for the UserTable query.
        """
        self.context_params = context_params
        self.command_params = command_params

    def transform_query(self):
        """
        Transform the command-specific parameters into a query.

        If command_params is not provided, it initializes a default UserTableQueryParams object.
        """
        if not self.command_params:
            self.command_params = None
            # Set Default Arguments
            self.command_params: UserTableQueryParams = UserTableQueryParams()
        else:
            self.command_params: UserTableQueryParams = UserTableQueryParams(
                **self.command_params
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
        self.toolbox = await generate_user_table_toolbox(
            symbols=self.context_params.symbols,
            user_role=self.command_params.user_role,
        )
        self.mandelbrot = self.toolbox.technical.mandelbrot_channel().to_polars(
            collect=False
        )
        return self

    async def transform_data(self):
        """
        Transform the command-specific data according to the user_table logic.

        Returns
        -------
        pl.DataFrame
            The transformed data as a Polars DataFrame
        """
        # Implement data transformation logic here
        transformed_data: pl.LazyFrame = await aggregate_user_table_data(
            symbols=self.context_params.symbols,
            etf_data=self.etf_data,
            mandelbrot_data=self.mandelbrot,
            toolbox=self.toolbox,
        )
        self.transformed_data = UserTableData(transformed_data)
        self.transformed_data = self.transformed_data
        return self

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
        self.transform_query()
        await self.extract_data()
        await self.transform_data()

        return HumblObject(
            results=self.transformed_data,
            provider=self.context_params.provider,
            warnings=None,
            chart=None,
            context_params=self.context_params,
            command_params=self.command_params,
        )
