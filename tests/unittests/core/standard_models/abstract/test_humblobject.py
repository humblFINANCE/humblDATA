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
    with open("tests/test_data/mandelbrot_humblobject.pkl", "rb") as file:
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


def test_to_json(humblobject: HumblObject):
    """Test HumblObject `.to_json()` method."""
    # Test with default parameters
    json_result = humblobject.to_json()
    assert isinstance(json_result, str)

    # Verify that the result is valid JSON
    import json

    try:
        json.loads(json_result)
    except json.JSONDecodeError:
        pytest.fail("Result is not valid JSON")

    # Test with equity_data=True
    json_result_equity = humblobject.to_json(equity_data=True)
    assert isinstance(json_result_equity, str)

    # Verify that the equity data result is valid JSON
    try:
        json.loads(json_result_equity)
    except json.JSONDecodeError:
        pytest.fail("Equity data result is not valid JSON")

    # Test with `chart=True`
    json_result_chart = humblobject.to_json(chart=True)
    assert isinstance(json_result_chart, list)

    # The str is being read as a dict...but it is a string

    # assert all(isinstance(item, str) for item in json_result_chart)

    # for chart in json_result_chart:
    #     try:
    #         json.dumps(chart, cls=PlotlyJSONEncoder)
    #     except json.JSONDecodeError:
    #         pytest.fail(f"Chart data result is not valid JSON: {chart}")

    # Optionally, you can add more specific checks on the content of the JSON
    # For example, checking if certain keys are present in the parsed JSON
    parsed_json = json.loads(json_result)
    assert isinstance(parsed_json, dict)  # Assuming the result is a JSON object

    # Add any other specific assertions based on the expected structure of your JSON output
