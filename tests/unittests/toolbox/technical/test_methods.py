import pytest
from src.humbldata.toolbox.technical.technical_controller import Technical

from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.standard_models.toolbox.technical.humbl_channel import (
    HumblChannelQueryParams,
)


@pytest.fixture
def context_params(request):
    return ToolboxQueryParams(
        symbol=request.param["symbol"],
        interval=request.param["interval"],
        start_date=request.param["start_date"],
        end_date=request.param["end_date"],
    )


@pytest.fixture
def command_params(request):
    return HumblChannelQueryParams(
        historical=request.param["historical"],
        window=request.param["window"],
        _boundary_group_down=request.param["_boundary_group_down"],
    )


@pytest.fixture
def technical(context_params):
    return Technical(context_params)


@pytest.mark.parametrize(
    "context_params, command_params",
    [
        (
            {
                "symbol": "AAPL",
                "interval": "1d",
                "start_date": "2022-01-01",
                "end_date": "2022-02-01",
            },
            {
                "historical": False,
                "window": "1m",
                "_boundary_group_down": False,
            },
        ),
        (
            {
                "symbol": "GOOGL",
                "interval": "1h",
                "start_date": "2022-03-01",
                "end_date": "2022-10-01",
            },
            {
                "historical": True,
                "window": "3m",
                "_boundary_group_down": True,
            },
        ),
    ],
    indirect=True,
)
@pytest.mark.skip(
    reason="Testing and comparing mocked objects to mocked objects"
)
# I need to mock external API calls and just test the internal logic
def test_humbl_channel_integration(
    mocker, technical, context_params, command_params
):
    # Arrange
    mock_humbl_object = mocker.Mock(spec=HumblObject)
    mock_humbl_object.context_params = context_params
    mock_humbl_object.command_params = command_params

    mocker.patch.object(
        technical, "humbl_channel", return_value=mock_humbl_object
    )

    # Act
    result = technical.humbl_channel(**command_params.model_dump())

    # Assert
    assert isinstance(result, HumblObject)
    assert result.context_params == context_params
    assert result.command_params == command_params
