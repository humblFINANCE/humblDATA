"""
UserTable Standard Model.

Context: Portfolio || Category: Analytics || Command: user_table.

This module is used to define the QueryParams and Data model for the
UserTable command.
"""

from typing import Literal, TypeVar

import pandera.polars as pa
import polars as pl

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.utils.descriptions import QUERY_DESCRIPTIONS


class ETFCategoryData(Data):
    """
    Data model for the etf_category command, a Pandera.Polars Model.

    Used for simple validation of ETF category data for the UserTableFetcher
    internal logic `aggregate_user_table_data()`
    """

    symbol: str = pa.Field(
        default=None,
        title="Symbol",
        description=QUERY_DESCRIPTIONS.get("symbol", ""),
    )
    category: pl.Utf8 | None = pa.Field(
        default=None,
        title="Category/Sector",
        description=QUERY_DESCRIPTIONS.get("category", ""),
        nullable=True,
    )
