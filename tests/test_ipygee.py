"""Test the ipygee package."""

import ee

import ipygee


def test_hello_world():
    """Hello world test."""
    assert ipygee.Hello().hello_world() == "hello world !"


def test_gee_connection():
    """Test the geeconnection is working."""
    assert ee.Number(1).getInfo() == 1
