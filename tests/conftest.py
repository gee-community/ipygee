"""Pytest session configuration."""

import pytest_gee


def pytest_configure():
    """Configure test environment."""
    pytest_gee.init_ee_from_token()
