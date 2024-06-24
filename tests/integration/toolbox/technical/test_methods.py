"""Testing Integration of passing parameters from Toolbox() to Technical() to MandelbrotChannelFetcher()."""

import pytest
from src.humbldata.toolbox.technical.technical_controller import Technical

from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.standard_models.toolbox.technical.mandelbrot_channel import (
    MandelbrotChannelQueryParams,
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
        symbol=request.param["symbol"],
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
    MandelbrotChannelQueryParams:
        The command parameters for the Mandelbrot Channel.
    """
    return MandelbrotChannelQueryParams(
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
def test_mandelbrot_channel_integration(
    technical, context_params, command_params
):
    """
    Test the integration of passing parameters.

    ToolboxQueryParams (context) and MandelbrotChannelQueryParams (command)
    parameters to the MandelbrotChannelFetcher,
    and comparing the parameters returned to the ones input.

    Args:
        technical: The Technical instance.
        context_params: The context parameters for the Toolbox.
        command_params: The command parameters for the Mandelbrot Channel.
    """
    # Act
    result = technical.mandelbrot_channel(**command_params.model_dump())

    # Assert
    assert isinstance(result, HumblObject)
    assert result.context_params == context_params
    assert result.command_params == command_params
