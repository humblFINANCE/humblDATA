import pickle

import pandas as pd
import polars as pl
import pyarrow as pa
import pytest
from pydantic import ValidationError

from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.toolbox import ToolboxQueryParams

pytestmark = [
    pytest.mark.slow(reason="HumblObject() pickling is slow to run??")
]


@pytest.fixture()
def humblobject():
    with open("tests/test_data/mandelbrot_current.pkl", "rb") as file:
        out = pickle.load(file)
        file.close()
    return out


def test_humblobject_params():
    assert isinstance(HumblObject().context_params, ToolboxQueryParams)
    assert HumblObject().command_params.__name__ == "QueryParams"


@pytest.mark.parametrize(
    ("provider_input", "expected_error"),
    [
        ("yfinance", None),
        ("fmp", None),
        ("intrinio", None),
        (2, ValidationError),
    ],
)
def test_humblobject_provider(provider_input, expected_error):
    if expected_error:
        with pytest.raises(expected_error):
            HumblObject(provider=provider_input).provider
    else:
        assert HumblObject(provider=provider_input).provider == provider_input


def test_to_polars(humblobject: HumblObject):
    """Test HumblObject `.to_polars()` method."""
    assert isinstance(humblobject.to_polars(collect=False), pl.LazyFrame)
    assert isinstance(humblobject.to_polars(collect=True), pl.DataFrame)

    assert isinstance(
        humblobject.to_polars(collect=False, equity_data=True), pl.LazyFrame
    )
    assert isinstance(
        humblobject.to_polars(collect=True, equity_data=True), pl.DataFrame
    )


def test_to_df(humblobject: HumblObject):
    """Test HumblObject `.to_df()` method."""
    assert isinstance(humblobject.to_df(collect=False), pl.LazyFrame)
    assert isinstance(humblobject.to_df(collect=True), pl.DataFrame)

    assert isinstance(
        humblobject.to_df(collect=False, equity_data=True), pl.LazyFrame
    )
    assert isinstance(
        humblobject.to_df(collect=True, equity_data=True), pl.DataFrame
    )


def test_to_pandas(humblobject: HumblObject):
    """Test HumblObject `.to_pandas()` method."""
    assert isinstance(humblobject.to_pandas(), pd.DataFrame)
    assert isinstance(humblobject.to_pandas(equity_data=True), pd.DataFrame)


def test_to_dict(humblobject: HumblObject):
    """Test HumblObject `.to_dict()` method."""
    assert isinstance(humblobject.to_dict(), dict)
    assert isinstance(humblobject.to_dict(equity_data=True), dict)
    assert isinstance(humblobject.to_dict(row_wise=True), list)
    assert isinstance(humblobject.to_dict(row_wise=True)[0], dict)


def test_to_arrow(humblobject: HumblObject):
    """Test HumblObject `.to_arrow()` method."""
    assert isinstance(humblobject.to_arrow(), pa.Table)
    assert isinstance(humblobject.to_arrow(equity_data=True), pa.Table)


def test_to_struct(humblobject: HumblObject):
    """Test HumblObject `.to_struct()` method."""
    assert isinstance(humblobject.to_struct(), pl.Series)
    assert isinstance(humblobject.to_struct(equity_data=True), pl.Series)
