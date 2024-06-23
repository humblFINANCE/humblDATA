
"""
PortfolioTable Standard Model.

Context: Portfolio || Category: Analytics || Command: PortfolioTable.

This module is used to define the QueryParams and Data model for the
PortfolioTable command.
"""

from typing import Literal

from pydantic import Field, field_validator

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.query_params import QueryParams

PORTFOLIOTABLE_QUERY_DESCRIPTIONS = {
    "example_field1": "Description for example field 1",
    "example_field2": "Description for example field 2",
}


class PortfolioTableQueryParams(QueryParams):
    """
    QueryParams model for the PortfolioTable command, a Pydantic v2 model.

    Parameters
    ----------
    example_field1 : str
        An example field.
    example_field2 : bool
        Another example field.
    """

    example_field1: str = Field(
        default="default_value",
        title="Example Field 1",
        description=PORTFOLIOTABLE_QUERY_DESCRIPTIONS.get("example_field1", ""),
    )
    example_field2: bool = Field(
        default=True,
        title="Example Field 2",
        description=PORTFOLIOTABLE_QUERY_DESCRIPTIONS.get("example_field2", ""),
    )

    @field_validator("example_field1", mode="after")
    @classmethod
    def validate_example_field1(cls, v: str) -> str:
        # Add any validation logic here
        return v


class PortfolioTableData(Data):
    """
    Data model for the PortfolioTable command, a Pandera.Polars Model.

    Parameters
    ----------
    # Add your data model parameters here
    """

    # Add your data model fields here
