"""Testing Integration of passing parameters from Toolbox() to Technical() to HumblChannelFetcher()."""

import pytest
from src.humbldata.toolbox.technical.technical_controller import Technical

from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.standard_models.toolbox.technical.humbl_channel import (
    HumblChannelQueryParams,
)
from humbldata.core.standard_models.toolbox.technical.humbl_momentum import (
    HumblMomentumQueryParams,
)


@pytest.fixture
def context_params(request):
    """
    Fixture to provide context parameters for the Toolbox.

    Args
    ----
        request: The pytest request object containing the parameters.

    Returns
    -------
    ToolboxQueryParams:
        The context parameters for the Toolbox.
    """
    return ToolboxQueryParams(
        symbols=request.param["symbol"],
        interval=request.param["interval"],
        start_date=request.param["start_date"],
        end_date=request.param["end_date"],
    )


@pytest.fixture
def command_params(request):
    """
    Fixture to provide command parameters for the Mandelbrot Channel.

    Args
    ----
        request: The pytest request object containing the parameters.


    Returns
    -------
    HumblChannelQueryParams:
        The command parameters for the Mandelbrot Channel.
    """
    return HumblChannelQueryParams(
        historical=request.param["historical"],
        window=request.param["window"],
        _boundary_group_down=request.param["_boundary_group_down"],
    )


@pytest.fixture
def technical(context_params):
    """
    Fixture to provide an instance of the Technical class.

    Args:
        context_params: The context parameters for the Toolbox.

    Returns
    -------
    Technical:
        An instance of the Technical class.
    """
    return Technical(context_params)


@pytest.fixture
def momentum_command_params(request):
    """
    Fixture to provide command parameters for the Momentum calculations.

    Args
    ----
        request: The pytest request object containing the parameters.

    Returns
    -------
    HumblMomentumQueryParams:
        The command parameters for Momentum calculations.
    """
    return HumblMomentumQueryParams(
        method=request.param["method"],
        window=request.param["window"],
        chart=request.param["chart"],
        template=request.param["template"],
    )


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
def test_humbl_channel_integration(technical, context_params, command_params):
    """
    Test the integration of passing parameters.

    ToolboxQueryParams (context) and HumblChannelQueryParams (command)
    parameters to the HumblChannelFetcher,
    and comparing the parameters returned to the ones input.

    Args:
        technical: The Technical instance.
        context_params: The context parameters for the Toolbox.
        command_params: The command parameters for the Mandelbrot Channel.
    """
    # Act
    result = technical.humbl_channel(**command_params.model_dump())

    # Assert
    assert isinstance(result, HumblObject)
    assert result.context_params == context_params
    assert result.command_params == command_params


@pytest.mark.parametrize(
    "context_params, momentum_command_params",
    [
        (
            {
                "symbol": "AAPL",
                "interval": "1d",
                "start_date": "2022-01-01",
                "end_date": "2022-02-01",
            },
            {
                "method": "log",
                "window": "14d",
                "chart": False,
                "template": "humbl_dark",
            },
        ),
        (
            {
                "symbol": "GOOGL",
                "interval": "1h",
                "start_date": "2022-03-01",
                "end_date": "2022-04-01",
            },
            {
                "method": "simple",
                "window": "20d",
                "chart": True,
                "template": "humbl_light",
            },
        ),
        (
            {
                "symbol": "MSFT",
                "interval": "1d",
                "start_date": "2022-05-01",
                "end_date": "2022-06-01",
            },
            {
                "method": "shift",
                "window": "5d",
                "chart": False,
                "template": "plotly_dark",
            },
        ),
    ],
    indirect=True,
)
def test_momentum_integration(
    technical, context_params, momentum_command_params
):
    """
    Test the integration of passing parameters from Toolbox to Technical to HumblMomentumFetcher.

    Tests that both ToolboxQueryParams (context) and HumblMomentumQueryParams (command)
    parameters are correctly passed through to the HumblMomentumFetcher and returned
    in the result.

    Args:
        technical: The Technical instance
        context_params: The context parameters for the Toolbox
        momentum_command_params: The command parameters for Momentum calculations
    """
    # Act
    result = technical.humbl_momentum(**momentum_command_params.model_dump())

    # Assert
    assert isinstance(result, HumblObject)
    assert result.context_params == context_params
    assert result.command_params == momentum_command_params
