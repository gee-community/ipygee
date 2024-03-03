"""All the map related widgets and functions are here."""
from __future__ import annotations

import geemap

from .sidecar import HasSideCar


class Map(geemap.Map, HasSideCar):
    """A subclass of geemap.Map with a sidecar method."""

    sidecar_title = "Map"
    "title of the sidecar"
