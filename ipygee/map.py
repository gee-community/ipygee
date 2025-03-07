"""All the map related widgets and functions are here."""
from __future__ import annotations

from geemap import core

from .sidecar import HasSideCar


class Map(core.Map, HasSideCar):
    """A subclass of geemap.Map with a sidecar method."""

    sidecar_title = "Map"
    "title of the sidecar"
