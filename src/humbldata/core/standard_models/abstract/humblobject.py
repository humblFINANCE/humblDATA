import io
from typing import Any, ClassVar, Generic, TypeVar

import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa
from pydantic import BaseModel, Field, PrivateAttr

from humbldata.core.standard_models.abstract.chart import Chart
from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.core.standard_models.abstract.tagged import Tagged
from humbldata.core.standard_models.abstract.warnings import Warning_

T = TypeVar("T")


class HumblObject(Tagged, Generic[T]):
    """HumblObject is the base class for all dta returned from the Toolbox."""

    _user_settings: ClassVar[BaseModel | None] = None
    _system_settings: ClassVar[BaseModel | None] = None

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

    _context_params: dict[str, Any] | None = PrivateAttr(
        default_factory=dict,
    )
    _command_params: dict[str, Any] | None = PrivateAttr(
        default_factory=dict,
    )

    def __repr__(self) -> str:
        """Human readable representation of the object."""
        items = [
            f"{k}: {v}"[:83] + ("..." if len(f"{k}: {v}") > 83 else "")
            for k, v in self.model_dump().items()
        ]
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

    def show(self) -> None:
        """Show the chart."""
        if not self.chart or not self.chart.fig:
            raise HumblDataError("Chart not found.")
        raise NotImplementedError
