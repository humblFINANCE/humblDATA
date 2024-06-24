
"""
Context: Portfolio || **Category: Standardized Framework Model**.

This module defines the QueryParams and Data classes for the portfolio context.
"""

from typing import Optional

from pydantic import Field, field_validator

from humbldata.core.standard_models.abstract.data import Data
from humbldata.core.standard_models.abstract.query_params import QueryParams


class PortfolioQueryParams(QueryParams):
    """
    Query parameters for the portfolioController.

    This class defines the query parameters used by the portfolioController.

    Parameters
    ----------
    example_field1 : str
        An example field.
    example_field2 : Optional[int]
        Another example field.
    """

    example_field1: str = Field(
        default="default_value",
        title="Example Field 1",
        description="Description for example field 1",
    )
    example_field2: Optional[int] = Field(
        default=None,
        title="Example Field 2",
        description="Description for example field 2",
    )

    @field_validator("example_field1")
    @classmethod
    def validate_example_field1(cls, v: str) -> str:
        return v.upper()


class PortfolioData(Data):
    """
    The Data for the PortfolioController.
    """

    # Add your data model fields here
    pass
