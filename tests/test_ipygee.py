"""Test the ipygee package."""

import ee


def test_gee_connection():
    """Test the geeconnection is working."""
    assert ee.Number(1).getInfo() == 1
