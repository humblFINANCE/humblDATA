"""Test humbldata."""

import humbldata


def test_import() -> None:
    """Test that the package can be imported."""
    assert isinstance(humbldata.__name__, str)
