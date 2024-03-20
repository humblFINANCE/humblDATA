import io
from typing import Any, ClassVar, Generic, Type, TypeVar

import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator

from humbldata.core.standard_models.abstract.chart import Chart
from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.abstract.tagged import Tagged
from humbldata.core.standard_models.abstract.warnings import Warning_
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.standard_models.toolbox.technical.mandelbrot_channel import (
    MandelbrotChannelQueryParams,
)

T = TypeVar("T")


def extract_subclass_dict(self, attribute_name: str, items: list):
    """
    Extract the dictionary representation of the specified attribute.

    Parameters
    ----------
    attribute_name : str
        The name of the attribute to update in the items list.
    """
    # Check if the attribute exists and has a value
    attribute_value = getattr(self, attribute_name, None)
    if attribute_value:
        # Assuming the attribute has a method called 'model_dump' to get its dictionary representation
        add_item = attribute_value.model_dump()
        for i, item in enumerate(items):
            if item.startswith(f"{attribute_name}:"):
                items[i] = f"{attribute_name}: {add_item}"
                break

    return items


class HumblObject(Tagged, Generic[T]):
    """HumblObject is the base class for all dta returned from the Toolbox."""

    _user_settings: ClassVar[BaseModel | None] = None
    _system_settings: ClassVar[BaseModel | None] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    results: T | None = Field(
        default=None,
        description="Serializable Logical Plan of the pl.LazyFrame results.",
    )
    provider: str | None = Field(
        default=None,
        description="Provider name.",
    )
    warnings: list[Warning_] | None = Field(
        default=None,
        description="List of warnings.",
    )
    chart: Chart | None = Field(
        default=None,
        description="Chart object.",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Extra info.",
    )
    context_params: ToolboxQueryParams | None = Field(
        default_factory=ToolboxQueryParams,
    )
    command_params: QueryParams | None = Field()

    # @field_validator("command_params")
    # def validate_command_params(cls, v):
    #     class_name = v.__class__.__name__
    #     if "QueryParams" in class_name:
    #         return v
    #     msg = "Wrong type for 'command_params', must be subclass of QueryParams"
    #     raise TypeError(msg)

    def __repr__(self) -> str:
        """Human readable representation of the object."""
        items = [
            f"{k}: {v}"[:83] + ("..." if len(f"{k}: {v}") > 83 else "")
            for k, v in self.model_dump().items()
        ]

        # Needed to extract subclass dict correctly
        items = extract_subclass_dict(self, "command_params", items)

        return f"{self.__class__.__name__}\n\n" + "\n".join(items)

    def to_polars(self, *, collect: bool = True) -> pl.LazyFrame | pl.DataFrame:
        """
        Deserialize the stored results and optionally collect them into a Polars DataFrame.

        Parameters
        ----------
        collect : bool, optional
            If True, collects the deserialized LazyFrame into a DataFrame.
            Default is True.

        Returns
        -------
        pl.LazyFrame | pl.DataFrame
            The deserialized results as a Polars LazyFrame or DataFrame,
            depending on the collect parameter.

        Raises
        ------
        HumblDataError
            If no results are found to deserialize
        """
        if self.results is None or not self.results:
            raise HumblDataError("No results found.")

        if collect:
            out = pl.LazyFrame.deserialize(io.StringIO(self.results)).collect()
        else:
            out = pl.LazyFrame.deserialize(io.StringIO(self.results))
        return out

    def to_df(self, *, collect: bool = True) -> pl.LazyFrame | pl.DataFrame:
        """
        Alias for the `to_polars` method.

        Parameters
        ----------
        collect : bool, optional
            If True, collects the deserialized LazyFrame into a DataFrame.
            Default is True.

        Returns
        -------
        pl.LazyFrame | pl.DataFrame
            The deserialized results as a Polars LazyFrame or DataFrame,
            depending on the collect parameter.
        """
        return self.to_polars(collect=collect)

    def to_pandas(self) -> pd.DataFrame:
        """
        Convert the results to a Pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            The results as a Pandas DataFrame.
        """
        return self.to_polars(collect=True).to_pandas()

    def to_numpy(self) -> np.ndarray:
        """
        Convert the results to a NumPy array.

        Returns
        -------
        np.ndarray
            The results as a NumPy array.
        """
        return self.to_polars(collect=True).to_numpy()

    def to_dict(self, *, row_wise: bool = False) -> dict:
        """
        Convert the results to a dictionary.

        Parameters
        ----------
        row_wise : bool, optional
            If True, convert every row to a dictionary of Python-native values.
            If False, convert DataFrame to a dictionary, mapping column name to
            values. Default is False.

        Returns
        -------
        dict
            The results as a dictionary.
        """
        if row_wise:
            return self.to_polars(collect=True).to_dicts()
        return self.to_polars(collect=True).to_dict()

    def to_arrow(self) -> pa.Table:
        """
        Convert the results to an Arrow Table.

        Returns
        -------
        pa.Table
            The results as an Arrow Table.
        """
        return self.to_polars(collect=True).to_arrow()

    def to_struct(self, name: str = "results") -> pl.Series:
        """
        Convert the results to a struct.

        Parameters
        ----------
        name : str, optional
            The name of the struct. Default is "results".

        Returns
        -------
        pl.Struct
            The results as a struct.
        """
        return self.to_polars(collect=True).to_struct(name=name)

    def is_empty(self) -> bool:
        """
        Check if the results are empty.

        Returns
        -------
        bool
            True if the results are empty, False otherwise.
        """
        return self.to_polars(collect=True).is_empty()

    def show(self) -> None:
        """Show the chart."""
        if not self.chart or not self.chart.fig:
            raise HumblDataError("Chart not found.")
        raise NotImplementedError
