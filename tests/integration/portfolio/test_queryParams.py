"""Testing parameter/field validation for PortfolioQueryParams."""

from typing import get_args
import pytest
from humbldata.core.standard_models.portfolio import PortfolioQueryParams
from humbldata.core.utils.constants import OBB_EQUITY_PRICE_HISTORICAL_PROVIDERS


@pytest.mark.parametrize(
    ("input", "expected"),
    [
        ("aapl", ["AAPL"]),
        ("aapl,msft", ["AAPL", "MSFT"]),
        ("aapl, msft", ["AAPL", "MSFT"]),
        ("AAPL,msft, GOOG", ["AAPL", "MSFT", "GOOG"]),
        (["aapl"], ["AAPL"]),
        (["aapl", "msft"], ["AAPL", "MSFT"]),
        (["aapl", "MSFT"], ["AAPL", "MSFT"]),
        (["aapl", "msFT", "amd", "TSla"], ["AAPL", "MSFT", "AMD", "TSLA"]),
        ({"aapl", "msft"}, ["AAPL", "MSFT"]),
        (["aapl", " "], ["AAPL"]),
    ],
)
def test_portfolio_symbol_validator(input, expected):
    """Test symbol validation and conversion to uppercase."""
    portfolio = PortfolioQueryParams(symbols=input)
    assert set(portfolio.symbols) == set(expected)


@pytest.mark.parametrize(
    "invalid_input",
    [
        123,
        ["aapl", 123],
        ["aapl", None],
    ],
)
def test_portfolio_symbol_validator_error(invalid_input):
    """Test invalid symbol inputs."""
    with pytest.raises((TypeError, AttributeError)):
        PortfolioQueryParams(symbols=invalid_input)


def test_portfolio_default_values():
    """Test default values for PortfolioQueryParams."""
    params = PortfolioQueryParams()
    assert params.symbols == ["AAPL"]
    assert params.provider == "yfinance"
    assert params.membership == "anonymous"


@pytest.mark.parametrize(
    "provider", list(get_args(OBB_EQUITY_PRICE_HISTORICAL_PROVIDERS))
)
def test_portfolio_provider_validator(provider):
    """Test valid provider inputs."""
    params = PortfolioQueryParams(provider=provider)
    assert params.provider == provider


@pytest.mark.parametrize(
    "membership",
    ["humblPEON", "humblPREMIUM", "humblPOWER", "humblPERMANENT", "admin"],
)
def test_portfolio_membership_validator(membership):
    """Test valid user role inputs."""
    params = PortfolioQueryParams(membership=membership)
    assert params.membership == membership


@pytest.mark.parametrize("invalid_input", ["basic", "super_admin", "user"])
def test_portfolio_membership_validator_error(invalid_input):
    """Test invalid user role inputs."""
    with pytest.raises(ValueError):
        PortfolioQueryParams(membership=invalid_input)
