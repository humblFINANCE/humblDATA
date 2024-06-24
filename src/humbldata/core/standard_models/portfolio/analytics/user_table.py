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
from humbldata.core.utils.descriptions import QUERY_DESCRIPTIONS
from humbldata.core.utils.openbb_helpers import get_latest_price, get_sector
from humbldata.toolbox.toolbox_controller import Toolbox

Q = TypeVar("Q", bound=PortfolioQueryParams)

USERTABLE_QUERY_DESCRIPTIONS = {
    "example_field1": "Description for example field 1",
    "example_field2": "Description for example field 2",
}


class UserTableQueryParams(QueryParams):
    """
    QueryParams model for the UserTable command, a Pydantic v2 model.

    Parameters
    ----------
    symbol : str | list[str] | set[str], default=""
        The symbol or ticker of the stock. You can pass multiple tickers like:
        "AAPL", "AAPL, MSFT" or ["AAPL", "MSFT"]. The input will be converted
        to a comma separated string of uppercase symbols : ['AAPL', 'MSFT']
    """

    symbol: str | list[str] | set[str] = pa.Field(
        default="AAPL",
        title="Symbol",
        description="The stock symbol or ticker",
    )
    user_role: Literal["basic", "premium", "power", "admin"] = Field(
        default="basic",
        title="User Role",
        description=QUERY_DESCRIPTIONS.get("user_role", ""),
    )

    @field_validator("symbol", mode="before", check_fields=False)
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
        description="The stock symbol or ticker",
    )
    last_price: pl.Float64 = pa.Field(
        default=None,
        title="Last Price",
        description="The most recent price of the asset",
    )
    buy_price: pl.Float64 = pa.Field(
        default=None,
        title="Buy Price",
        description="The recommended buy price for the asset",
    )
    sell_price: pl.Float64 = pa.Field(
        default=None,
        title="Sell Price",
        description="The recommended sell price for the asset",
    )
    up_down: pl.Utf8 = pa.Field(
        default=None,
        title="Up/Down",
        description="Indicator of price movement (up or down)",
    )
    risk_reward: pl.Float64 = pa.Field(
        default=None,
        title="Risk/Reward",
        description="The risk-reward ratio for the asset",
    )
    asset_class: pl.Utf8 = pa.Field(
        default=None,
        title="Asset Class",
        description="The class of the asset (e.g., equity, bond, commodity)",
    )
    sector: pl.Utf8 = pa.Field(
        default=None,
        title="Sector",
        description="The sector to which the asset belongs",
    )
    humbl_suggestion: pl.Utf8 = pa.Field(
        default=None,
        title="humblSuggestion",
        description="humbl's recommendation for the asset",
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

    def extract_data(self):
        """
        Extract the data from the provider and returns it as a Polars DataFrame.

        Returns
        -------
        pl.DataFrame
            The extracted data as a Polars DataFrame.
        """
        # Setup Toolbox
        # TODO: make different toolboxes for different user_roles
        # TODO: have different date collection for different users

        toolbox = Toolbox(
            symbol=self.context_params.symbol,
            interval="1d",
            start_date="2020-01-01",
            end_date="2024-01-01",
        )

        # Get last_price from OpenBB
        last_prices_df = get_latest_price(
            symbol=self.context_params.symbol,
            provider=self.context_params.provider,
        )
        # Get Mandelbrot Data
        mandelbrot_df = toolbox.technical.mandelbrot_channel(
            window="1m", historical=True
        )

        # Get sector Data
        sectors_df = get_sector(symbols=self.context_params.symbol)

        self.data = pl.DataFrame()
        return self

    def transform_data(self):
        """
        Transform the command-specific data according to the user_table logic.

        Returns
        -------
        pl.DataFrame
            The transformed data as a Polars DataFrame
        """
        # Implement data transformation logic here
        self.transformed_data = UserTableData(self.data)
        self.transformed_data = self.transformed_data.serialize()
        return self

    def fetch_data(self):
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
        self.extract_data()
        self.transform_data()

        return HumblObject(
            results=self.transformed_data,
            provider=self.context_params.provider,
            warnings=None,
            chart=None,
            context_params=self.context_params,
            command_params=self.command_params,
        )
